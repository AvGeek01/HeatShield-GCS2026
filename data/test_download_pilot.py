"""Unit tests for pilot download geometry and output-path safety."""

from pathlib import Path

from data.download_pilot import PILOT_SIDE_METERS, UTM_EPSG, pilot_bounds
from heatcore.data.config import RAW_DATA_DIR, REPOSITORY_ROOT


def test_pilot_bounds_are_a_five_kilometer_square() -> None:
    """Projecting the returned bbox back to UTM yields the configured side length."""
    from pyproj import Transformer

    west, south, east, north = pilot_bounds()
    to_utm = Transformer.from_crs("EPSG:4326", UTM_EPSG, always_xy=True)
    lower_left = to_utm.transform(west, south)
    upper_right = to_utm.transform(east, north)

    assert abs(upper_right[0] - lower_left[0] - PILOT_SIDE_METERS) < 0.01
    assert abs(upper_right[1] - lower_left[1] - PILOT_SIDE_METERS) < 0.01


def test_raw_data_path_is_inside_repository() -> None:
    """Raw downloads resolve relative to the script, not the shell's working folder."""
    assert RAW_DATA_DIR == Path(REPOSITORY_ROOT, "data", "raw")
