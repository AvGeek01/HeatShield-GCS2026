"""Verify locally cached pilot datasets against their manifest and bbox."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import rasterio
from pyproj import Geod, Transformer

from heatcore.data.config import (
    EXPECTED_DATA_FILES,
    LANDSAT_FILE,
    OSM_FILE,
    PILOT_CENTER_LATITUDE,
    PILOT_CENTER_LONGITUDE,
    RAW_DATA_DIR,
    SENTINEL_FILE,
    WEATHER_FILE,
    WORLDPOP_FILE,
    pilot_bounds,
)

MANIFEST_NAME = "manifest.json"
MANIFEST_FIELDS = (
    "source",
    "dataset_id",
    "bbox_wsen",
    "date_range",
    "crs",
    "resolution",
    "license",
    "sha256",
    "downloaded_at_utc",
)
BBOX_TOLERANCE_DEGREES = 1e-5
MAX_FORECAST_GRID_OFFSET_METERS = 30_000


def _sha256(path: Path) -> str:
    """Calculate a file checksum without reading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _matches_pilot_bbox(
    actual_bbox: tuple[float, float, float, float],
    expected_bbox: tuple[float, float, float, float],
) -> bool:
    """Return whether an extent covers the expected WGS84 pilot bbox."""
    west, south, east, north = actual_bbox
    expected_west, expected_south, expected_east, expected_north = expected_bbox
    return (
        west <= expected_west + BBOX_TOLERANCE_DEGREES
        and south <= expected_south + BBOX_TOLERANCE_DEGREES
        and east >= expected_east - BBOX_TOLERANCE_DEGREES
        and north >= expected_north - BBOX_TOLERANCE_DEGREES
    )


def _verify_raster(
    path: Path,
    entry: dict[str, Any],
    bbox: tuple[float, float, float, float],
) -> list[str]:
    """Check a raster's CRS, recorded metadata, and coverage of the pilot bbox."""
    errors: list[str] = []
    with rasterio.open(path) as dataset:
        if dataset.crs is None:
            return [f"{path.name}: raster has no CRS."]
        if not dataset.dataset_mask().any():
            errors.append(f"{path.name}: raster has no valid pixels.")
        actual_crs = dataset.crs.to_string()
        if actual_crs != entry.get("crs"):
            errors.append(
                f"{path.name}: CRS is {actual_crs}, manifest declares {entry.get('crs')}."
            )
        transformer = Transformer.from_crs(
            dataset.crs, "EPSG:4326", always_xy=True
        )
        actual_bbox = transformer.transform_bounds(
            *dataset.bounds, densify_pts=21
        )
        if not _matches_pilot_bbox(actual_bbox, bbox):
            errors.append(
                f"{path.name}: raster extent {actual_bbox} does not cover "
                f"pilot bbox {bbox}."
            )
        recorded_bounds = entry.get("raster_bounds")
        if not isinstance(recorded_bounds, list) or len(recorded_bounds) != 4:
            errors.append(f"{path.name}: manifest raster_bounds is missing or invalid.")
        elif any(
            not math.isclose(actual, recorded, abs_tol=1e-6)
            for actual, recorded in zip(dataset.bounds, recorded_bounds)
        ):
            errors.append(f"{path.name}: raster_bounds do not match the file.")
        resolution = entry.get("resolution")
        if (
            not isinstance(resolution, list)
            or len(resolution) != 2
            or any(
                not math.isclose(abs(actual), recorded, abs_tol=1e-6)
                for actual, recorded in zip(dataset.res, resolution)
            )
        ):
            errors.append(f"{path.name}: resolution does not match the raster.")
    return errors


def _verify_weather(
    path: Path,
    entry: dict[str, Any],
    bbox: tuple[float, float, float, float],
) -> list[str]:
    """Check that the cached hourly forecast has valid times and a pilot location."""
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{path.name}: invalid forecast JSON: {error}."]
    if not isinstance(payload, dict):
        return [f"{path.name}: forecast JSON is not an object."]
    hourly = payload.get("hourly")
    times = hourly.get("time") if isinstance(hourly, dict) else None
    if not isinstance(times, list) or not times:
        return [f"{path.name}: hourly forecast times are missing."]
    west, south, east, north = bbox
    requested_location = entry.get("requested_location_wgs84")
    if (
        not isinstance(requested_location, list)
        or len(requested_location) != 2
        or not south <= requested_location[0] <= north
        or not west <= requested_location[1] <= east
    ):
        errors.append(f"{path.name}: requested forecast point is outside the pilot bbox.")
    elif requested_location != [
        PILOT_CENTER_LATITUDE,
        PILOT_CENTER_LONGITUDE,
    ]:
        errors.append(f"{path.name}: requested point is not the configured pilot center.")
    response_location = (payload.get("latitude"), payload.get("longitude"))
    if (
        not all(isinstance(value, (int, float)) for value in response_location)
        or not isinstance(requested_location, list)
        or len(requested_location) != 2
    ):
        errors.append(f"{path.name}: forecast response location is missing or invalid.")
    else:
        recorded_response = entry.get("response_grid_point_wgs84")
        if recorded_response != list(response_location):
            errors.append(
                f"{path.name}: response grid point differs from the manifest."
            )
        distance_meters = Geod(ellps="WGS84").inv(
            requested_location[1],
            requested_location[0],
            response_location[1],
            response_location[0],
        )[2]
        if distance_meters > MAX_FORECAST_GRID_OFFSET_METERS:
            errors.append(
                f"{path.name}: forecast grid point is {distance_meters:.0f} m "
                "from the requested pilot center."
            )
    if payload.get("heatshield_pilot_bbox_wgs84") != list(bbox):
        errors.append(f"{path.name}: cached pilot bbox does not match the manifest.")
    return errors


def verify_data(raw_dir: Path = RAW_DATA_DIR) -> bool:
    """Print PASS or FAIL after checking files, hashes, metadata, and bbox coverage."""
    manifest_path = raw_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        print(f"FAIL: missing {manifest_path}")
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot read {manifest_path}: {error}")
        return False
    if not isinstance(manifest, dict):
        print(f"FAIL: {manifest_path} must contain a JSON object.")
        return False

    errors: list[str] = []
    try:
        expected_bbox = pilot_bounds()
    except RuntimeError as error:
        print(f"FAIL: {error}")
        return False
    declared_bbox = manifest.get("pilot_bbox_wsen")
    if not isinstance(declared_bbox, list) or len(declared_bbox) != 4:
        errors.append("Manifest pilot_bbox_wsen is missing or invalid.")
    elif any(
        not math.isclose(actual, expected, abs_tol=1e-9)
        for actual, expected in zip(declared_bbox, expected_bbox)
    ):
        errors.append("Manifest bbox does not match the configured DTU pilot bbox.")

    files = manifest.get("files")
    if not isinstance(files, dict):
        print("FAIL: manifest files section is missing or invalid.")
        return False
    missing_entries = sorted(set(EXPECTED_DATA_FILES) - set(files))
    if missing_entries:
        errors.append(f"Manifest entries missing: {', '.join(missing_entries)}.")

    for name in EXPECTED_DATA_FILES:
        path = raw_dir / name
        entry = files.get(name)
        if not path.is_file():
            errors.append(f"Missing expected file: {name}.")
            continue
        if not isinstance(entry, dict):
            errors.append(f"{name}: manifest entry is missing or invalid.")
            continue
        missing_fields = [field for field in MANIFEST_FIELDS if field not in entry]
        if missing_fields:
            errors.append(
                f"{name}: missing manifest fields: {', '.join(missing_fields)}."
            )
            continue
        if entry.get("bbox_wsen") != declared_bbox:
            errors.append(f"{name}: bbox metadata differs from the manifest bbox.")
        if entry.get("sha256") != _sha256(path):
            errors.append(f"{name}: SHA-256 checksum mismatch.")
        if name in (LANDSAT_FILE, SENTINEL_FILE, WORLDPOP_FILE):
            errors.extend(_verify_raster(path, entry, expected_bbox))
        elif name == WEATHER_FILE:
            errors.extend(_verify_weather(path, entry, expected_bbox))
        elif name == OSM_FILE:
            try:
                collection = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                errors.append(f"{name}: invalid GeoJSON: {error}.")
            else:
                if not isinstance(collection, dict):
                    errors.append(f"{name}: GeoJSON is not an object.")
                    continue
                features = collection.get("features")
                if (
                    collection.get("type") != "FeatureCollection"
                    or not isinstance(features, list)
                    or not features
                ):
                    errors.append(f"{name}: GeoJSON has no features.")

    if errors:
        print("FAIL: pilot data verification found issues:")
        for error in errors:
            print(f" - {error}")
        return False
    print(
        "PASS: all expected pilot data files match their manifest checksums "
        "and cover the DTU/Rohini bbox."
    )
    return True


def main() -> int:
    """Run local pilot-data verification as a command-line module."""
    return 0 if verify_data() else 1


if __name__ == "__main__":
    raise SystemExit(main())
