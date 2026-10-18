"""Shared spatial and output configuration for Delhi pilot data."""

from pathlib import Path

PILOT_CENTER_LATITUDE = 28.7501
PILOT_CENTER_LONGITUDE = 77.1177
PILOT_SIDE_METERS = 5_000
UTM_EPSG = "EPSG:32643"

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = REPOSITORY_ROOT / "data" / "raw"
LANDSAT_FILE = "landsat_lst_celsius.tif"
SENTINEL_FILE = "sentinel2_ndvi.tif"
WORLDPOP_FILE = "worldpop_2020_1km.tif"
WEATHER_FILE = "open_meteo_forecast.json"
OSM_FILE = "osm_features.geojson"
MANIFEST_FILE = "manifest.json"
EXPECTED_DATA_FILES = (
    WEATHER_FILE,
    WORLDPOP_FILE,
    OSM_FILE,
    LANDSAT_FILE,
    SENTINEL_FILE,
)


def pilot_bounds() -> tuple[float, float, float, float]:
    """Return the 5 km pilot square as a WGS84 bbox (west, south, east, north)."""
    try:
        from pyproj import Transformer
    except ImportError as error:
        raise RuntimeError(
            "Install the geospatial dependencies from data/README.md."
        ) from error

    to_utm = Transformer.from_crs("EPSG:4326", UTM_EPSG, always_xy=True)
    to_wgs84 = Transformer.from_crs(UTM_EPSG, "EPSG:4326", always_xy=True)
    center_x, center_y = to_utm.transform(
        PILOT_CENTER_LONGITUDE, PILOT_CENTER_LATITUDE
    )
    half_side = PILOT_SIDE_METERS / 2
    corners = (
        to_wgs84.transform(center_x - half_side, center_y - half_side),
        to_wgs84.transform(center_x + half_side, center_y + half_side),
    )
    west, south = corners[0]
    east, north = corners[1]
    return west, south, east, north
