"""Download pilot-area weather, satellite, population, and OpenStreetMap data."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import planetary_computer
import rasterio
import requests
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.warp import reproject
from rasterio.windows import Window, from_bounds

from heatcore.data.config import (
    EXPECTED_DATA_FILES,
    LANDSAT_FILE,
    OSM_FILE,
    PILOT_CENTER_LATITUDE,
    PILOT_CENTER_LONGITUDE,
    PILOT_SIDE_METERS,
    RAW_DATA_DIR,
    SENTINEL_FILE,
    UTM_EPSG,
    WEATHER_FILE,
    WORLDPOP_FILE,
    pilot_bounds,
)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
STAC_SEARCH_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
WORLDPOP_URL = (
    "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/"
    "2020/IND/ind_ppp_2020_1km_Aggregated.tif"
)
HTTP_TIMEOUT_SECONDS = 120
STAC_PAGE_SIZE = 100
MAX_STAC_ITEMS = 500
OVERPASS_MAX_ATTEMPTS = 4
OVERPASS_INITIAL_RETRY_SECONDS = 5
SATELLITE_LOOKBACK_DAYS = 365
WORLDPOP_YEAR = 2020
LANDSAT_LICENSE = (
    "Upstream USGS Landsat Collection 2 data are public domain; acknowledge "
    "USGS/NASA. Planetary Computer STAC metadata says 'proprietary'; review "
    "hosting-service terms separately before redistribution."
)
SENTINEL_LICENSE = (
    "Copernicus Sentinel data are free and open under the Sentinel Data Legal "
    "Notice; provide source attribution. Planetary Computer STAC metadata says "
    "'proprietary'; review hosting-service terms separately before redistribution."
)


def _write_bytes_if_missing(path: Path, content: bytes) -> None:
    """Atomically write bytes without replacing an existing local file."""
    if path.exists():
        print(f"Using existing {path.name}")
        return

    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=f".{path.name}.", suffix=".part", delete=False
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
    try:
        with temporary_path.open("wb") as output:
            output.write(content)
        temporary_path.rename(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _read_url(url: str) -> bytes:
    """Read a URL and return its response body, raising on network or HTTP errors."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "HeatShield-GCS2026 pilot data downloader"}
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise RuntimeError(f"Unexpected HTTP status {response.status} for {url}")
        return response.read()


def download_weather(bounds: tuple[float, float, float, float]) -> None:
    """Download a seven-day Open-Meteo forecast for the pilot-area center."""
    target = RAW_DATA_DIR / WEATHER_FILE
    if target.exists():
        print(f"Using existing {target.name}")
        return

    parameters = urllib.parse.urlencode(
        {
            "latitude": PILOT_CENTER_LATITUDE,
            "longitude": PILOT_CENTER_LONGITUDE,
            "hourly": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "precipitation,wind_speed_10m,shortwave_radiation"
            ),
            "forecast_days": 7,
            "timezone": "Asia/Kolkata",
        }
    )
    payload = json.loads(_read_url(f"{FORECAST_URL}?{parameters}"))
    if "hourly" not in payload:
        raise RuntimeError("Open-Meteo response did not contain hourly forecast data.")
    payload["heatshield_pilot_bbox_wgs84"] = list(bounds)
    _write_bytes_if_missing(
        target, json.dumps(payload, indent=2).encode("utf-8")
    )
    print(f"Downloaded {target.name}")


def download_openstreetmap(
    bounds: tuple[float, float, float, float],
) -> None:
    """Download tagged OSM features for the pilot bbox using OSMnx/Overpass."""
    target = RAW_DATA_DIR / OSM_FILE
    if target.exists():
        print(f"Using existing {target.name}")
        return

    try:
        import osmnx as ox
        from osmnx._errors import ResponseStatusCodeError
    except ImportError as error:
        raise RuntimeError("Install the geospatial dependencies from data/README.md.") from error

    west, south, east, north = bounds
    for attempt in range(OVERPASS_MAX_ATTEMPTS):
        try:
            features = ox.features_from_bbox(
                bbox=(west, south, east, north),
                tags={
                    "amenity": True,
                    "building": True,
                    "highway": True,
                    "landuse": True,
                    "leisure": True,
                    "natural": True,
                },
            )
        except ResponseStatusCodeError as error:
            if attempt + 1 == OVERPASS_MAX_ATTEMPTS:
                raise RuntimeError(
                    "Overpass remained unavailable after "
                    f"{OVERPASS_MAX_ATTEMPTS} attempts; rerun later or use a "
                    "local OSM PBF extract."
                ) from error
            delay = OVERPASS_INITIAL_RETRY_SECONDS * (2**attempt)
            print(f"Overpass is unavailable; retrying in {delay} seconds.")
            time.sleep(delay)
        else:
            break
    if features.empty:
        raise RuntimeError("OpenStreetMap returned no tagged features for the pilot bbox.")
    _write_bytes_if_missing(target, features.to_json().encode("utf-8"))
    print(f"Downloaded {target.name}")


def download_worldpop(bounds: tuple[float, float, float, float]) -> None:
    """Download and crop the 2020 WorldPop 1 km India raster to the pilot bbox."""
    target = RAW_DATA_DIR / WORLDPOP_FILE
    if target.exists():
        print(f"Using existing {target.name}")
        return

    try:
        import rasterio
        from rasterio.mask import mask
    except ImportError as error:
        raise RuntimeError("Install the geospatial dependencies from data/README.md.") from error

    west, south, east, north = bounds
    geometry = {
        "type": "Polygon",
        "coordinates": [
            [
                [west, south],
                [east, south],
                [east, north],
                [west, north],
                [west, south],
            ]
        ],
    }

    with tempfile.TemporaryDirectory(
        prefix="worldpop-", dir=RAW_DATA_DIR
    ) as temporary_directory:
        source_path = Path(temporary_directory) / "india_worldpop.tif"
        source_path.write_bytes(_read_url(WORLDPOP_URL))
        with rasterio.open(source_path) as source:
            if source.crs is None:
                raise RuntimeError("WorldPop raster does not declare a coordinate system.")
            cropped, transform = mask(source, [geometry], crop=True)
            profile = source.profile.copy()
            profile.update(
                height=cropped.shape[1],
                width=cropped.shape[2],
                transform=transform,
                compress="deflate",
            )
            with tempfile.NamedTemporaryFile(
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".part",
                delete=False,
            ) as temporary_file:
                temporary_target = Path(temporary_file.name)
            try:
                with rasterio.open(temporary_target, "w", **profile) as output:
                    output.write(cropped)
                temporary_target.rename(target)
            finally:
                temporary_target.unlink(missing_ok=True)
    print(f"Downloaded and clipped {target.name}")


def _projected_bounds(
    bounds: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    """Project the WGS84 bbox to a densified UTM envelope."""
    transformer = Transformer.from_crs("EPSG:4326", UTM_EPSG, always_xy=True)
    return transformer.transform_bounds(*bounds, densify_pts=21)


def _search_stac_items(
    collection_id: str,
    bounds: tuple[float, float, float, float],
    start_date: str,
    end_date: str,
    *,
    cloud_cover_max: int | None = None,
) -> list[dict[str, Any]]:
    """Retrieve recent STAC items for a collection, following API pagination."""
    body: dict[str, Any] = {
        "collections": [collection_id],
        "bbox": list(bounds),
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "limit": STAC_PAGE_SIZE,
        "sortby": [{"field": "properties.datetime", "direction": "desc"}],
    }
    if cloud_cover_max is not None:
        body["query"] = {"eo:cloud_cover": {"lte": cloud_cover_max}}

    items: list[dict[str, Any]] = []
    next_request: tuple[str, str, dict[str, Any]] | None = (
        "POST",
        STAC_SEARCH_URL,
        body,
    )
    while next_request and len(items) < MAX_STAC_ITEMS:
        method, url, request_body = next_request
        if method == "POST":
            response = requests.post(
                url, json=request_body, timeout=HTTP_TIMEOUT_SECONDS
            )
        else:
            response = requests.get(url, timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        page = response.json()
        if not isinstance(page, dict) or not isinstance(page.get("features"), list):
            raise RuntimeError(
                f"Planetary Computer returned an invalid STAC response for {collection_id}."
            )
        items.extend(page["features"])
        next_link = next(
            (link for link in page.get("links", []) if link.get("rel") == "next"),
            None,
        )
        if next_link and len(items) >= MAX_STAC_ITEMS:
            raise RuntimeError(
                f"STAC collection {collection_id} exceeded the "
                f"{MAX_STAC_ITEMS}-item safety limit."
            )
        if next_link is None:
            next_request = None
        else:
            next_request = (
                next_link.get("method", "GET").upper(),
                next_link["href"],
                next_link.get("body", {}),
            )

    return items[:MAX_STAC_ITEMS]


def _read_window(
    asset_href: str,
    projected_bounds: tuple[float, float, float, float],
) -> tuple[np.ndarray, rasterio.Affine, dict[str, Any]]:
    """Read the minimal COG window intersecting projected pilot bounds."""
    signed_href = planetary_computer.sign_url(asset_href)
    with rasterio.open(signed_href) as source:
        if source.crs is None or source.crs.to_epsg() != 32643:
            raise RuntimeError(f"Unexpected source CRS for satellite asset: {source.crs}")
        requested_window = from_bounds(*projected_bounds, transform=source.transform)
        column_start = math.floor(requested_window.col_off)
        row_start = math.floor(requested_window.row_off)
        column_end = math.ceil(requested_window.col_off + requested_window.width)
        row_end = math.ceil(requested_window.row_off + requested_window.height)
        requested_window = Window(
            column_start,
            row_start,
            column_end - column_start,
            row_end - row_start,
        )
        window = requested_window.intersection(
            Window(0, 0, source.width, source.height)
        )
        if window.width <= 0 or window.height <= 0:
            raise RuntimeError("Satellite scene does not cover the pilot bbox.")
        data = source.read(1, window=window)
        return data, source.window_transform(window), source.profile.copy()


def _write_geotiff_if_missing(
    path: Path,
    array: np.ndarray,
    transform: rasterio.Affine,
    *,
    resolution_m: int,
    nodata: float,
) -> None:
    """Write one compressed, projected float GeoTIFF without replacing cached data."""
    if path.exists():
        print(f"Using existing {path.name}")
        return
    height, width = array.shape
    profile: dict[str, Any] = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": UTM_EPSG,
        "transform": transform,
        "nodata": nodata,
        "compress": "deflate",
        "predictor": 3,
        "tiled": True,
        "blockxsize": max(resolution_m, min(256, int(math.ceil(width / 16)) * 16)),
        "blockysize": max(resolution_m, min(256, int(math.ceil(height / 16)) * 16)),
    }
    for key in ("blockxsize", "blockysize"):
        profile[key] = max(16, profile[key] // 16 * 16)

    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=f".{path.name}.", suffix=".part", delete=False
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
    try:
        with rasterio.open(temporary_path, "w", **profile) as output:
            output.write(array.astype(np.float32, copy=False), 1)
        temporary_path.rename(path)
    finally:
        temporary_path.unlink(missing_ok=True)
    print(f"Downloaded {path.name}")


def _masked_median(arrays: list[np.ndarray]) -> np.ndarray:
    """Compute a per-cell median, retaining nodata where all scenes are masked."""
    stack = np.ma.masked_invalid(np.stack(arrays, axis=0))
    return np.ma.median(stack, axis=0).filled(-9999).astype(np.float32)


def _download_landsat_composite(
    items: list[dict[str, Any]],
    target: Path,
    projected_bounds: tuple[float, float, float, float],
) -> dict[str, Any]:
    """Create a cloud-masked annual median Landsat LST composite in Celsius."""
    if not items:
        raise RuntimeError("Planetary Computer returned no Landsat scenes for the bbox.")

    temperatures: list[np.ndarray] = []
    first_transform: rasterio.Affine | None = None
    first_profile: dict[str, Any] | None = None
    item_ids: list[str] = []
    dates: list[str] = []
    qa_cloud_bits = sum(1 << bit for bit in (0, 1, 2, 3, 4, 5))
    for item in items:
        assets = item.get("assets", {})
        if "lwir11" not in assets or "qa_pixel" not in assets:
            continue
        kelvin, transform, profile = _read_window(
            assets["lwir11"]["href"], projected_bounds
        )
        qa, qa_transform, _ = _read_window(
            assets["qa_pixel"]["href"], projected_bounds
        )
        if qa.shape != kelvin.shape or qa_transform != transform:
            raise RuntimeError("Landsat thermal and QA assets have misaligned grids.")
        valid = (kelvin != 0) & ((qa & qa_cloud_bits) == 0)
        temperature_c = kelvin.astype(np.float32) * 0.00341802 + 149.0 - 273.15
        temperatures.append(np.where(valid, temperature_c, np.nan))
        first_transform = first_transform or transform
        first_profile = first_profile or profile
        item_ids.append(item["id"])
        dates.append(item["properties"]["datetime"])

    if not temperatures or first_transform is None or first_profile is None:
        raise RuntimeError("No usable Landsat ST_B10 assets were found for the bbox.")
    shapes = {array.shape for array in temperatures}
    if len(shapes) != 1:
        raise RuntimeError("Landsat scenes use incompatible pixel grids for compositing.")
    if not target.exists():
        _write_geotiff_if_missing(
            target,
            _masked_median(temperatures),
            first_transform,
            resolution_m=30,
            nodata=-9999,
        )
    return {
        "dataset_id": "landsat-c2-l2",
        "item_ids": item_ids,
        "date_range": {
            "start": min(dates)[:10],
            "end": max(dates)[:10],
        },
        "crs": "EPSG:32643",
        "resolution_m": 30,
        "license": LANDSAT_LICENSE,
    }


def _read_sentinel_scene(
    item: dict[str, Any],
    projected_bounds: tuple[float, float, float, float],
) -> tuple[np.ndarray, rasterio.Affine, dict[str, Any]]:
    """Read Sentinel B04/B08 and cloud-masking SCL over the pilot bbox."""
    assets = item.get("assets", {})
    if not all(key in assets for key in ("B04", "B08", "SCL")):
        raise RuntimeError(f"Sentinel scene {item.get('id')} is missing required bands.")

    red, transform, profile = _read_window(
        assets["B04"]["href"], projected_bounds
    )
    nir, nir_transform, _ = _read_window(
        assets["B08"]["href"], projected_bounds
    )
    if nir.shape != red.shape or nir_transform != transform:
        raise RuntimeError("Sentinel B04 and B08 assets have misaligned grids.")

    with rasterio.open(planetary_computer.sign_url(assets["SCL"]["href"])) as source:
        scl = np.zeros(red.shape, dtype=np.uint8)
        reproject(
            source=rasterio.band(source, 1),
            destination=scl,
            src_transform=source.transform,
            src_crs=source.crs,
            dst_transform=transform,
            dst_crs=profile["crs"],
            resampling=Resampling.nearest,
        )
    denominator = nir.astype(np.float32) + red.astype(np.float32)
    valid = (denominator > 0) & ~np.isin(scl, (0, 3, 8, 9, 10, 11))
    ndvi = np.full(red.shape, np.nan, dtype=np.float32)
    ndvi[valid] = (
        nir[valid].astype(np.float32) - red[valid].astype(np.float32)
    ) / denominator[valid]
    return ndvi, transform, profile


def _download_sentinel_composite(
    items: list[dict[str, Any]],
    target: Path,
    projected_bounds: tuple[float, float, float, float],
) -> dict[str, Any]:
    """Create a cloud-masked annual median Sentinel-2 NDVI composite."""
    if not items:
        raise RuntimeError("Planetary Computer returned no Sentinel-2 scenes for the bbox.")

    indices: list[np.ndarray] = []
    first_transform: rasterio.Affine | None = None
    first_profile: dict[str, Any] | None = None
    item_ids: list[str] = []
    dates: list[str] = []
    for item in items:
        index, transform, profile = _read_sentinel_scene(item, projected_bounds)
        indices.append(index)
        first_transform = first_transform or transform
        first_profile = first_profile or profile
        item_ids.append(item["id"])
        dates.append(item["properties"]["datetime"])

    if first_transform is None or first_profile is None:
        raise RuntimeError("No usable Sentinel-2 surface reflectance scenes were found.")
    shapes = {array.shape for array in indices}
    if len(shapes) != 1:
        raise RuntimeError("Sentinel-2 scenes use incompatible pixel grids for compositing.")
    if not target.exists():
        _write_geotiff_if_missing(
            target,
            _masked_median(indices),
            first_transform,
            resolution_m=10,
            nodata=-9999,
        )
    return {
        "dataset_id": "sentinel-2-l2a",
        "item_ids": item_ids,
        "date_range": {
            "start": min(dates)[:10],
            "end": max(dates)[:10],
        },
        "crs": "EPSG:32643",
        "resolution_m": 10,
        "license": SENTINEL_LICENSE,
    }


def download_satellite_layers(
    bounds: tuple[float, float, float, float],
) -> dict[str, dict[str, Any]]:
    """Download satellite composites from public Planetary Computer STAC COGs."""
    start_date = (
        datetime.now(timezone.utc).date() - timedelta(days=SATELLITE_LOOKBACK_DAYS)
    ).isoformat()
    end_date = datetime.now(timezone.utc).date().isoformat()
    projected = _projected_bounds(bounds)
    landsat_target = RAW_DATA_DIR / LANDSAT_FILE
    sentinel_target = RAW_DATA_DIR / SENTINEL_FILE
    records: dict[str, dict[str, Any]] = {}
    current_manifest = _load_existing_manifest()
    targets = (
        (LANDSAT_FILE, landsat_target, "landsat-c2-l2", 30, LANDSAT_LICENSE),
        (SENTINEL_FILE, sentinel_target, "sentinel-2-l2a", 10, SENTINEL_LICENSE),
    )
    for name, target, dataset_id, resolution_m, license_text in targets:
        cached_record = (
            _satellite_record_from_manifest(current_manifest, name, target)
            if target.exists()
            else None
        )
        if cached_record is not None:
            print(f"Using existing {target.name}")
            records[name] = cached_record
            continue

        items = _search_stac_items(
            dataset_id,
            bounds,
            start_date,
            end_date,
            cloud_cover_max=80 if name == SENTINEL_FILE else None,
        )
        if name == LANDSAT_FILE:
            records[name] = _download_landsat_composite(
                items, target, projected
            )
        else:
            records[name] = _download_sentinel_composite(
                items, target, projected
            )
    for record in records.values():
        record.setdefault(
            "query_date_range", {"start": start_date, "end": end_date}
        )
    return records


def _load_existing_manifest() -> dict[str, Any] | None:
    """Load a prior manifest so existing satellite provenance can be reused."""
    manifest_path = RAW_DATA_DIR / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Cannot resume from invalid existing manifest {manifest_path}: {error}"
        ) from error
    if not isinstance(manifest, dict):
        raise RuntimeError(f"Existing manifest is not a JSON object: {manifest_path}")
    if not isinstance(manifest.get("files"), dict):
        raise RuntimeError(f"Existing manifest has no valid files section: {manifest_path}")
    return manifest


def _satellite_record_from_manifest(
    manifest: dict[str, Any] | None,
    name: str,
    path: Path,
) -> dict[str, Any] | None:
    """Recover prior satellite item metadata without refetching cached data."""
    if manifest is None:
        return None
    files = manifest.get("files")
    if not isinstance(files, dict):
        return None
    entry = files.get(name)
    if not isinstance(entry, dict):
        return None
    required = (
        "sha256",
        "dataset_id",
        "scene_ids",
        "date_range",
        "query_date_range",
        "crs",
        "license",
    )
    if any(key not in entry for key in required):
        return None
    if entry["sha256"] != _sha256(path):
        raise RuntimeError(
            f"Cached {name} does not match its manifest checksum; refusing to "
            "rewrite its provenance."
        )
    resolution_m = 30 if name == LANDSAT_FILE else 10
    return {
        "dataset_id": entry["dataset_id"],
        "item_ids": entry["scene_ids"],
        "date_range": entry["date_range"],
        "query_date_range": entry["query_date_range"],
        "crs": entry["crs"],
        "resolution_m": resolution_m,
        "license": entry["license"],
    }


def _sha256(path: Path) -> str:
    """Return a file's SHA-256 checksum using bounded-memory reads."""
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def _download_time(path: Path) -> str:
    """Return a cached file's last-modified time as an ISO-8601 UTC timestamp."""
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def _raster_metadata(path: Path) -> tuple[str, list[float], list[float]]:
    """Return a raster's CRS, bounds, and pixel resolution."""
    with rasterio.open(path) as dataset:
        if dataset.crs is None:
            raise RuntimeError(f"Raster does not declare a CRS: {path.name}")
        bounds = dataset.bounds
        resolution = dataset.res
        return (
            dataset.crs.to_string(),
            [bounds.left, bounds.bottom, bounds.right, bounds.top],
            [abs(resolution[0]), abs(resolution[1])],
        )


def _manifest_entry(
    path: Path,
    *,
    source: str,
    dataset_id: str,
    bounds: tuple[float, float, float, float],
    date_range: dict[str, str],
    crs: str,
    resolution: str | list[float],
    license_text: str,
) -> dict[str, Any]:
    """Create a complete provenance record for one cached dataset file."""
    return {
        "source": source,
        "dataset_id": dataset_id,
        "bbox_wsen": list(bounds),
        "date_range": date_range,
        "crs": crs,
        "resolution": resolution,
        "license": license_text,
        "sha256": _sha256(path),
        "downloaded_at_utc": _download_time(path),
    }


def write_manifest(
    bounds: tuple[float, float, float, float],
    satellite_records: dict[str, dict[str, Any]],
) -> None:
    """Write checksummed source metadata for every expected cached data file."""
    timestamp = datetime.now(timezone.utc).isoformat()
    weather_path = RAW_DATA_DIR / WEATHER_FILE
    weather = json.loads(weather_path.read_text(encoding="utf-8"))
    weather_times = weather["hourly"]["time"]
    weather_record = _manifest_entry(
        weather_path,
        source="Open-Meteo Forecast API",
        dataset_id="api.open-meteo.com/v1/forecast",
        bounds=bounds,
        date_range={"start": weather_times[0], "end": weather_times[-1]},
        crs="EPSG:4326 point forecast at pilot center",
        resolution="Hourly point series; model grid resolution varies",
        license_text=(
            "CC BY 4.0; attribute Open-Meteo, link the licence, and indicate "
            "modifications. Free endpoint is non-commercial and rate-limited."
        ),
    )
    weather_record["requested_location_wgs84"] = [
        PILOT_CENTER_LATITUDE,
        PILOT_CENTER_LONGITUDE,
    ]
    weather_record["response_grid_point_wgs84"] = [
        weather["latitude"],
        weather["longitude"],
    ]

    osm_path = RAW_DATA_DIR / OSM_FILE
    osm_record = _manifest_entry(
        osm_path,
        source="OpenStreetMap via OSMnx/Overpass API",
        dataset_id="OpenStreetMap",
        bounds=bounds,
        date_range={"start": _download_time(osm_path), "end": _download_time(osm_path)},
        crs="EPSG:4326",
        resolution="Vector features; no fixed raster resolution",
        license_text=(
            "Open Database License (ODbL) 1.0; attribute © OpenStreetMap "
            "contributors and comply with share-alike obligations."
        ),
    )

    worldpop_path = RAW_DATA_DIR / WORLDPOP_FILE
    worldpop_crs, worldpop_bounds, worldpop_resolution = _raster_metadata(
        worldpop_path
    )
    worldpop_record = _manifest_entry(
        worldpop_path,
        source="WorldPop India 2020 population count",
        dataset_id="WorldPop/Global_2000_2020_1km/2020/IND/ind_ppp_2020_1km_Aggregated",
        bounds=bounds,
        date_range={"start": str(WORLDPOP_YEAR), "end": str(WORLDPOP_YEAR)},
        crs=worldpop_crs,
        resolution=worldpop_resolution,
        license_text=(
            "No explicit licence was stated in the linked archive index; retain "
            "WorldPop attribution and verify product terms before redistribution."
        ),
    )
    worldpop_record["raster_bounds"] = worldpop_bounds

    entries: dict[str, Any] = {
        WEATHER_FILE: weather_record,
        OSM_FILE: osm_record,
        WORLDPOP_FILE: worldpop_record,
    }
    for name in (LANDSAT_FILE, SENTINEL_FILE):
        satellite_path = RAW_DATA_DIR / name
        record = satellite_records[name]
        raster_crs, raster_bounds, pixel_size = _raster_metadata(satellite_path)
        entry = _manifest_entry(
            satellite_path,
            source=(
                "Microsoft Planetary Computer STAC API; USGS Landsat Collection 2"
                if name == LANDSAT_FILE
                else "Microsoft Planetary Computer STAC API; Copernicus Sentinel-2 L2A"
            ),
            dataset_id=record["dataset_id"],
            bounds=bounds,
            date_range=record["date_range"],
            crs=raster_crs,
            resolution=pixel_size,
            license_text=record["license"],
        )
        entry["raster_bounds"] = raster_bounds
        entry["query_date_range"] = record["query_date_range"]
        entry["scene_count"] = len(record["item_ids"])
        entry["scene_ids"] = record["item_ids"]
        entries[name] = entry

    missing = [name for name in EXPECTED_DATA_FILES if name not in entries]
    if missing:
        raise RuntimeError(f"Manifest is missing expected files: {missing}")
    manifest = {
        "schema_version": 1,
        "created_at_utc": timestamp,
        "pilot_center_wgs84": [PILOT_CENTER_LATITUDE, PILOT_CENTER_LONGITUDE],
        "pilot_bbox_wsen": list(bounds),
        "pilot_side_meters_utm": PILOT_SIDE_METERS,
        "utm_crs": UTM_EPSG,
        "files": entries,
    }

    target = RAW_DATA_DIR / "manifest.json"
    with tempfile.NamedTemporaryFile(
        dir=target.parent, prefix=f".{target.name}.", suffix=".part", delete=False
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
    try:
        with temporary_path.open("w", encoding="utf-8") as output:
            json.dump(manifest, output, indent=2)
            output.write("\n")
        temporary_path.replace(target)
    finally:
        temporary_path.unlink(missing_ok=True)
    print(f"Wrote {target.name}")


def main() -> None:
    """Download pilot inputs and record their spatial and source metadata."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    bounds = pilot_bounds()
    download_weather(bounds)
    download_worldpop(bounds)
    download_openstreetmap(bounds)
    satellite_records = download_satellite_layers(bounds)
    write_manifest(bounds, satellite_records)


if __name__ == "__main__":
    main()
