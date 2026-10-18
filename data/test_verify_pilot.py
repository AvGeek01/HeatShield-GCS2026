"""Tests for the local pilot-data manifest verifier."""

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin

from heatcore.data.config import (
    EXPECTED_DATA_FILES,
    LANDSAT_FILE,
    OSM_FILE,
    SENTINEL_FILE,
    WEATHER_FILE,
    WORLDPOP_FILE,
    pilot_bounds,
)
from heatcore.data.verify import verify_data

TEST_RASTER_SIZE = 100


def _write_raster(
    path: Path,
    bbox: tuple[float, float, float, float],
    crs: str,
    resolution: int,
) -> list[float]:
    """Create a test raster that fully covers the pilot bbox."""
    west, south, east, north = bbox
    if crs != "EPSG:4326":
        transform_bbox = Transformer.from_crs(
            "EPSG:4326", crs, always_xy=True
        )
        west, south, east, north = transform_bbox.transform_bounds(
            west, south, east, north, densify_pts=21
        )
    pixel = resolution
    width = int(np.ceil((east - west) / pixel)) + 2
    height = int(np.ceil((north - south) / pixel)) + 2
    transform = from_origin(west - pixel, north + pixel, pixel, pixel)
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "nodata": -9999.0,
    }
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(np.ones((height, width), dtype=np.float32), 1)
    with rasterio.open(path) as dataset:
        return list(dataset.bounds)


def _write_fixture(raw_dir: Path) -> dict[str, object]:
    """Write complete tiny pilot-cache fixtures and a matching manifest."""
    bbox = pilot_bounds()
    raw_dir.mkdir(parents=True, exist_ok=True)
    weather_path = raw_dir / WEATHER_FILE
    weather_path.write_text(
        json.dumps(
            {
                "latitude": 28.7501,
                "longitude": 77.1177,
                "hourly": {"time": ["2026-10-19T00:00"]},
                "heatshield_pilot_bbox_wgs84": list(bbox),
            }
        ),
        encoding="utf-8",
    )
    osm_path = raw_dir / OSM_FILE
    osm_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [77.1177, 28.7501]},
                        "properties": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    resolutions = {
        WORLDPOP_FILE: ("EPSG:4326", 0.001),
        LANDSAT_FILE: ("EPSG:32643", 30),
        SENTINEL_FILE: ("EPSG:32643", 10),
    }
    entries: dict[str, dict[str, object]] = {}
    for name in EXPECTED_DATA_FILES:
        path = raw_dir / name
        raster_bounds = None
        if name in resolutions:
            crs, resolution = resolutions[name]
            raster_bounds = _write_raster(path, bbox, crs, resolution)
            with rasterio.open(path) as dataset:
                pixel_size = list(dataset.res)
        elif name not in (WEATHER_FILE, OSM_FILE):
            raise AssertionError(f"Unhandled test fixture {name}")
        else:
            pixel_size = "Hourly point series" if name == WEATHER_FILE else "Vector"

        entry: dict[str, object] = {
            "source": "test fixture",
            "dataset_id": "test",
            "bbox_wsen": list(bbox),
            "date_range": {"start": "2026-10-19", "end": "2026-10-19"},
            "crs": resolutions[name][0] if name in resolutions else "EPSG:4326",
            "resolution": pixel_size,
            "license": "test",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "downloaded_at_utc": "2026-10-19T00:00:00+00:00",
        }
        if raster_bounds is not None:
            entry["raster_bounds"] = raster_bounds
        if name == WEATHER_FILE:
            entry["requested_location_wgs84"] = [28.7501, 77.1177]
            entry["response_grid_point_wgs84"] = [28.7501, 77.1177]
        entries[name] = entry

    manifest: dict[str, object] = {"pilot_bbox_wsen": list(bbox), "files": entries}
    (raw_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


def test_verifier_passes_complete_cache(tmp_path: Path, capsys) -> None:
    """A complete cache with matching hashes and covering rasters passes."""
    _write_fixture(tmp_path)

    assert verify_data(tmp_path)
    assert "PASS:" in capsys.readouterr().out


def test_verifier_fails_when_file_checksum_changes(tmp_path: Path, capsys) -> None:
    """Editing a cached file after manifest creation fails verification."""
    _write_fixture(tmp_path)
    weather = tmp_path / WEATHER_FILE
    weather.write_text(weather.read_text(encoding="utf-8") + " ", encoding="utf-8")

    assert not verify_data(tmp_path)
    assert f"{WEATHER_FILE}: SHA-256 checksum mismatch." in capsys.readouterr().out


def test_verifier_fails_when_expected_file_is_missing(
    tmp_path: Path, capsys
) -> None:
    """Every file in the declared pilot data set is required."""
    _write_fixture(tmp_path)
    (tmp_path / SENTINEL_FILE).unlink()

    assert not verify_data(tmp_path)
    assert f"Missing expected file: {SENTINEL_FILE}." in capsys.readouterr().out
