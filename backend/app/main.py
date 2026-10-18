"""HeatShield mock API for the Delhi pilot."""

from __future__ import annotations

import math
import os
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DEFAULT_BBOX = (77.04, 28.70, 77.14, 28.78)
ACTIVITY_MULTIPLIER = {
    "walking": 1.0,
    "commuting": 0.95,
    "cycling": 1.15,
    "running": 1.3,
    "outdoor_work": 1.2,
    "resting": 0.65,
}
PROFILE_ADJUSTMENT = {
    "general": 0,
    "child": 10,
    "older_adult": 12,
    "outdoor_worker": 8,
    "chronic_condition": 12,
}


class ResourceType(StrEnum):
    WATER = "water"
    SHADE = "shade"
    COOLING = "cooling"


class Location(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class RiskResponse(BaseModel):
    risk_score: float = Field(ge=0, le=100)
    level: Literal["low", "moderate", "high", "extreme"]
    wbgt_c: float = Field(ge=-50, le=80)
    factors: list[str]
    actions: list[str]


class PointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]


class LineStringGeometry(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: list[tuple[float, float]]


class HeatCellProperties(BaseModel):
    cell_id: str
    risk: float = Field(ge=0, le=100)
    temp_c: float = Field(ge=-50, le=80)
    wbgt_c: float = Field(ge=-50, le=80)
    population_exposed: int = Field(ge=0)


class HeatCellFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: PointGeometry
    properties: HeatCellProperties


class HeatmapResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[HeatCellFeature]


class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: Location
    dest: Location
    activity: Literal["walking", "commuting", "cycling", "running", "outdoor_work", "resting"] = "walking"


class RouteOption(BaseModel):
    geometry: LineStringGeometry
    duration_min: float = Field(gt=0)
    exposure: float = Field(ge=0, le=100)


class RouteResponse(BaseModel):
    fastest: RouteOption
    coolest: RouteOption


class Resource(BaseModel):
    resource_id: str
    type: ResourceType
    name: str
    location: Location
    distance_m: float = Field(ge=0)
    availability: Literal["open", "limited", "unknown"]


class ResourcesResponse(BaseModel):
    resources: list[Resource]


class OptimizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget_inr: float = Field(gt=0, le=1_000_000_000)
    bbox: list[float] = Field(min_length=4, max_length=4)

    @field_validator("bbox", mode="before")
    @classmethod
    def parse_bbox(cls, value: object) -> object:
        if isinstance(value, str):
            try:
                value = [float(bound.strip()) for bound in value.split(",")]
            except ValueError as exc:
                raise ValueError("bbox must be four comma-separated numbers or a four-number array") from exc
        return value

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, value: list[float]) -> list[float]:
        min_lon, min_lat, max_lon, max_lat = value
        if not (-180 <= min_lon < max_lon <= 180):
            raise ValueError("bbox longitude bounds must be ordered within [-180, 180]")
        if not (-90 <= min_lat < max_lat <= 90):
            raise ValueError("bbox latitude bounds must be ordered within [-90, 90]")
        return value


class Intervention(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cell_id: str = Field(min_length=1)
    type: ResourceType
    units: int = Field(default=1, ge=1, le=100)


class InterventionPlanItem(BaseModel):
    intervention: ResourceType
    units: int = Field(ge=1)
    cost_inr: float = Field(ge=0)
    expected_risk_reduction: float = Field(ge=0, le=100)


class RankedHotspot(BaseModel):
    rank: int = Field(ge=1)
    cell_id: str
    risk: float = Field(ge=0, le=100)
    population_exposed: int = Field(ge=0)
    interventions: list[InterventionPlanItem]


class InterventionSummary(BaseModel):
    name: str
    locations: int = Field(ge=0)
    cost_inr: float = Field(ge=0)


class OptimizeResponse(BaseModel):
    ranked_hotspots: list[RankedHotspot]
    total_cost_inr: float = Field(ge=0)
    expected_risk_reduction: float = Field(ge=0)
    budget_inr: float = Field(ge=0)
    people_reached: int = Field(ge=0)
    population_exposed: int = Field(ge=0)
    interventions: list[InterventionSummary]


class SimulateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interventions: list[Intervention] = Field(max_length=100)


class ReadingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    ts: datetime
    temp_c: float = Field(ge=-50, le=80)
    rh: float = Field(ge=0, le=100)
    lux: float = Field(ge=0, le=200_000)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class ReadingResponse(BaseModel):
    accepted: bool
    node_id: str
    received_at: datetime


class BoundingBox(BaseModel):
    bounds: tuple[float, float, float, float]

    @model_validator(mode="after")
    def validate_bounds(self) -> BoundingBox:
        min_lon, min_lat, max_lon, max_lat = self.bounds
        if not (-180 <= min_lon < max_lon <= 180):
            raise ValueError("bbox longitude bounds must be ordered within [-180, 180]")
        if not (-90 <= min_lat < max_lat <= 90):
            raise ValueError("bbox latitude bounds must be ordered within [-90, 90]")
        return self


def _level(score: float) -> Literal["low", "moderate", "high", "extreme"]:
    if score < 25:
        return "low"
    if score < 50:
        return "moderate"
    if score < 75:
        return "high"
    return "extreme"


def _mock_weather(lat: float, lon: float) -> tuple[float, float]:
    distance = math.hypot(lat - 28.75, (lon - 77.10) * 0.8)
    temp_c = 36.5 - min(distance * 8, 2.0)
    wbgt_c = temp_c - 3.0
    return round(temp_c, 1), round(wbgt_c, 1)


def _risk_value(lat: float, lon: float, activity: str, duration_min: int, profile: str) -> float:
    temp_c, _ = _mock_weather(lat, lon)
    base = 28 + max(0, temp_c - 32) * 5
    activity_factor = ACTIVITY_MULTIPLIER[activity]
    duration_factor = min(duration_min / 60, 2.0)
    score = base * activity_factor * duration_factor + PROFILE_ADJUSTMENT[profile]
    return round(min(100, max(0, score)), 1)


def _parse_query_bbox(raw_bbox: str) -> BoundingBox:
    try:
        values = [float(value.strip()) for value in raw_bbox.split(",")]
        return BoundingBox(bounds=tuple(values))
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=422,
            detail="bbox must be min_lon,min_lat,max_lon,max_lat with valid WGS84 bounds",
        ) from exc


def _cell_id(row: int, column: int, bounds: tuple[float, float, float, float]) -> str:
    encoded_bounds = ":".join(repr(bound) for bound in bounds)
    return f"delhi:v1:{row}:{column}:{encoded_bounds}"


def _cell_bounds(cell_id: str) -> tuple[float, float, float, float]:
    legacy_parts = cell_id.split("-")
    if len(legacy_parts) == 3 and legacy_parts[0] == "delhi":
        try:
            row, column = map(int, legacy_parts[1:])
        except ValueError:
            row, column = -1, -1
        if row in (0, 1) and column in (0, 1):
            return DEFAULT_BBOX

    parts = cell_id.split(":")
    if len(parts) != 8 or parts[:2] != ["delhi", "v1"]:
        raise ValueError(f"Invalid heatmap cell_id: {cell_id}")
    try:
        row, column = int(parts[2]), int(parts[3])
        bounds = tuple(float(bound) for bound in parts[4:])
        validated_bounds = BoundingBox(bounds=bounds).bounds
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid heatmap cell_id: {cell_id}") from exc
    if row not in (0, 1) or column not in (0, 1):
        raise ValueError(f"Invalid heatmap cell_id: {cell_id}")
    return validated_bounds


def _heatmap(bounds: tuple[float, float, float, float]) -> HeatmapResponse:
    min_lon, min_lat, max_lon, max_lat = bounds
    lon_step = (max_lon - min_lon) / 2
    lat_step = (max_lat - min_lat) / 2
    features: list[HeatCellFeature] = []
    for row in range(2):
        for column in range(2):
            west = min_lon + column * lon_step
            south = min_lat + row * lat_step
            east = west + lon_step
            north = south + lat_step
            center_lat = (south + north) / 2
            center_lon = (west + east) / 2
            temp_c, wbgt_c = _mock_weather(center_lat, center_lon)
            risk = round(min(100, max(0, 40 + (temp_c - 33) * 8 + row * 3 + column * 2)), 1)
            cell_id = _cell_id(row, column, bounds)
            features.append(
                HeatCellFeature(
                    geometry=PointGeometry(coordinates=(center_lon, center_lat)),
                    properties=HeatCellProperties(
                        cell_id=cell_id,
                        risk=risk,
                        temp_c=temp_c,
                        wbgt_c=wbgt_c,
                        population_exposed=450 + row * 240 + column * 170,
                    ),
                )
            )
    return HeatmapResponse(features=features)


def _distance_m(origin: Location, destination: Location) -> float:
    earth_radius_m = 6_371_000
    lat1, lat2 = math.radians(origin.lat), math.radians(destination.lat)
    delta_lat = lat2 - lat1
    delta_lon = math.radians(destination.lon - origin.lon)
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    return earth_radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


app = FastAPI(
    title="HeatShield API",
    description=(
        "Mock heat-risk and city-planning API for the Delhi pilot. Responses are "
        "synthetic examples, not live forecasts, verified resources, or medical advice."
    ),
    version="0.1.0",
)

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/risk", response_model=RiskResponse, tags=["Personal risk"])
def get_risk(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    activity: Literal["walking", "commuting", "cycling", "running", "outdoor_work", "resting"],
    duration_min: Annotated[int, Query(ge=1, le=720)],
    profile: Literal["general", "child", "older_adult", "outdoor_worker", "chronic_condition", "worker"] = "general",
) -> RiskResponse:
    risk_profile = "outdoor_worker" if profile == "worker" else profile
    score = _risk_value(lat, lon, activity, duration_min, risk_profile)
    temp_c, wbgt_c = _mock_weather(lat, lon)
    factors = [f"Synthetic air temperature: {temp_c:.1f} C", f"Planned activity: {activity}"]
    if duration_min >= 60:
        factors.append("Longer outdoor exposure increases the mock score")
    if profile != "general":
        factors.append("The selected profile adds a mock sensitivity adjustment")
    actions = ["Prefer shade and water breaks", "Reduce or reschedule strenuous outdoor activity"]
    if score < 25:
        actions = ["Stay hydrated", "Take breaks if conditions change"]
    return RiskResponse(
        risk_score=score,
        level=_level(score),
        wbgt_c=wbgt_c,
        factors=factors,
        actions=actions,
    )


@app.get("/api/heatmap", response_model=HeatmapResponse, tags=["City planning"])
def get_heatmap(
    bbox: Annotated[str, Query(description="min_lon,min_lat,max_lon,max_lat (WGS84)")],
    ts: datetime | Literal["latest"] | None = Query(
        default=None, description="Requested timestamp, or 'latest' for the current mock snapshot"
    ),
) -> HeatmapResponse:
    _ = ts or datetime.now(UTC)
    return _heatmap(_parse_query_bbox(bbox).bounds)


@app.post("/api/route", response_model=RouteResponse, tags=["Personal risk"])
def post_route(request: RouteRequest) -> RouteResponse:
    distance = _distance_m(request.origin, request.dest)
    midpoint = ((request.origin.lat + request.dest.lat) / 2, (request.origin.lon + request.dest.lon) / 2)
    detour = Location(
        lat=max(-90, min(90, midpoint[0] + 0.003)),
        lon=max(-180, min(180, midpoint[1] - 0.002)),
    )
    fastest_duration = max(1.0, distance / 75)
    coolest_distance = _distance_m(request.origin, detour) + _distance_m(detour, request.dest)
    return RouteResponse(
        fastest=RouteOption(
            geometry=LineStringGeometry(
                coordinates=[(request.origin.lon, request.origin.lat), (request.dest.lon, request.dest.lat)]
            ),
            duration_min=round(fastest_duration, 1),
            exposure=round(min(100, 48 * ACTIVITY_MULTIPLIER[request.activity]), 1),
        ),
        coolest=RouteOption(
            geometry=LineStringGeometry(
                coordinates=[
                    (request.origin.lon, request.origin.lat),
                    (detour.lon, detour.lat),
                    (request.dest.lon, request.dest.lat),
                ]
            ),
            duration_min=round(max(fastest_duration, coolest_distance / 65), 1),
            exposure=round(min(100, 29 * ACTIVITY_MULTIPLIER[request.activity]), 1),
        ),
    )


@app.get("/api/resources", response_model=ResourcesResponse, tags=["City planning"])
def get_resources(
    type: ResourceType,
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    radius_m: Annotated[float, Query(gt=0, le=50_000)] = 2_000,
) -> ResourcesResponse:
    candidates = [
        Resource(
            resource_id=f"mock-{type.value}-01",
            type=type,
            name=f"Mock {type.value} point 1",
            location=Location(lat=28.751, lon=77.116),
            distance_m=0,
            availability="unknown",
        ),
        Resource(
            resource_id=f"mock-{type.value}-02",
            type=type,
            name=f"Mock {type.value} point 2",
            location=Location(lat=28.735, lon=77.092),
            distance_m=0,
            availability="unknown",
        ),
    ]
    for resource in candidates:
        resource.distance_m = round(_distance_m(Location(lat=lat, lon=lon), resource.location), 1)
    return ResourcesResponse(resources=[item for item in candidates if item.distance_m <= radius_m])


@app.post("/api/interventions/optimize", response_model=OptimizeResponse, tags=["City planning"], include_in_schema=False)
@app.post("/api/optimize", response_model=OptimizeResponse, tags=["City planning"])
def post_optimize(request: OptimizeRequest) -> OptimizeResponse:
    cells = _heatmap(tuple(request.bbox)).features
    unit_cost = {ResourceType.WATER: 18_000, ResourceType.SHADE: 42_000, ResourceType.COOLING: 95_000}
    hotspots = sorted(cells, key=lambda cell: cell.properties.risk, reverse=True)
    ranked: list[RankedHotspot] = []
    remaining = request.budget_inr
    total_cost = 0.0
    total_reduction = 0.0
    for rank, cell in enumerate(hotspots, start=1):
        intervention = next(
            (kind for kind in (ResourceType.SHADE, ResourceType.WATER, ResourceType.COOLING)
             if unit_cost[kind] <= remaining),
            None,
        )
        items: list[InterventionPlanItem] = []
        if intervention is not None:
            cost = float(unit_cost[intervention])
            reduction = round(min(15, cell.properties.risk * 0.18), 1)
            items.append(
                InterventionPlanItem(
                    intervention=intervention,
                    units=1,
                    cost_inr=cost,
                    expected_risk_reduction=reduction,
                )
            )
            total_cost += cost
            total_reduction += reduction
            remaining -= cost
        ranked.append(
            RankedHotspot(
                rank=rank,
                cell_id=cell.properties.cell_id,
                risk=cell.properties.risk,
                population_exposed=cell.properties.population_exposed,
                interventions=items,
            )
        )
    by_type: dict[ResourceType, tuple[int, float]] = {}
    for hotspot in ranked:
        for item in hotspot.interventions:
            units, cost = by_type.get(item.intervention, (0, 0.0))
            by_type[item.intervention] = (units + item.units, cost + item.cost_inr)
    intervention_names = {
        ResourceType.SHADE: "Temporary shade points",
        ResourceType.WATER: "Water refill stations",
        ResourceType.COOLING: "Cooling centers",
    }
    return OptimizeResponse(
        ranked_hotspots=ranked,
        total_cost_inr=total_cost,
        expected_risk_reduction=round(total_reduction, 1),
        budget_inr=request.budget_inr,
        people_reached=sum(
            hotspot.population_exposed for hotspot in ranked if hotspot.interventions
        ),
        population_exposed=sum(hotspot.population_exposed for hotspot in ranked),
        interventions=[
            InterventionSummary(name=intervention_names[kind], locations=units, cost_inr=cost)
            for kind, (units, cost) in by_type.items()
        ],
    )


@app.post("/api/simulate", response_model=HeatmapResponse, tags=["City planning"])
def post_simulate(request: SimulateRequest) -> HeatmapResponse:
    if not request.interventions:
        return _heatmap(DEFAULT_BBOX)
    try:
        intervention_bounds = {_cell_bounds(item.cell_id) for item in request.interventions}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if len(intervention_bounds) != 1:
        raise HTTPException(status_code=422, detail="All simulation interventions must target the same bbox")
    heatmap = _heatmap(next(iter(intervention_bounds)))
    valid_cell_ids = {feature.properties.cell_id for feature in heatmap.features}
    unknown_cell_ids = sorted(
        {item.cell_id for item in request.interventions if item.cell_id not in valid_cell_ids}
    )
    if unknown_cell_ids:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown simulation cell_id(s): {', '.join(unknown_cell_ids)}",
        )
    reductions: dict[str, float] = {}
    reduction_by_type = {ResourceType.WATER: 3.0, ResourceType.SHADE: 7.0, ResourceType.COOLING: 11.0}
    for intervention in request.interventions:
        reductions[intervention.cell_id] = reductions.get(intervention.cell_id, 0) + (
            reduction_by_type[intervention.type] * intervention.units
        )
    for feature in heatmap.features:
        properties = feature.properties
        properties.risk = round(max(0, properties.risk - reductions.get(properties.cell_id, 0)), 1)
    return heatmap


@app.post("/api/readings", response_model=ReadingResponse, status_code=202, tags=["Sensor readings"])
def post_reading(request: ReadingRequest) -> ReadingResponse:
    return ReadingResponse(accepted=True, node_id=request.node_id, received_at=datetime.now(UTC))


@app.get("/health", tags=["Operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "mock"}