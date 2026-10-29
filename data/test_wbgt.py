"""Reference tests for the heatcore WBGT approximation."""

import pytest

from heatcore.wbgt import calculate_wbgt


@pytest.mark.parametrize(
    ("conditions", "expected_wbgt_c"),
    [
        (
            {
                "temp_c": 30.0,
                "relative_humidity_pct": 50.0,
                "wind_speed_m_s": 1.0,
                "solar_radiation_w_m2": 0.0,
            },
            24.6,
        ),
        (
            {
                "temp_c": 35.0,
                "relative_humidity_pct": 60.0,
                "wind_speed_m_s": 1.0,
                "solar_radiation_w_m2": 800.0,
            },
            32.7,
        ),
    ],
)
def test_calculate_wbgt_matches_reference_values(
    conditions: dict[str, float],
    expected_wbgt_c: float,
) -> None:
    """Known meteorological conditions produce the expected WBGT estimate."""
    assert calculate_wbgt(**conditions) == pytest.approx(expected_wbgt_c, abs=0.1)


def test_solar_load_increases_estimated_wbgt() -> None:
    """Direct solar load raises the estimated outdoor WBGT."""
    conditions = {
        "temp_c": 35.0,
        "relative_humidity_pct": 50.0,
        "wind_speed_m_s": 1.0,
    }
    shaded_wbgt = calculate_wbgt(**conditions, solar_radiation_w_m2=0.0)
    sunny_wbgt = calculate_wbgt(**conditions, solar_radiation_w_m2=800.0)

    assert sunny_wbgt > shaded_wbgt


@pytest.mark.parametrize(
    ("input_name", "input_value"),
    [
        ("relative_humidity_pct", 0.0),
        ("wind_speed_m_s", -0.1),
        ("solar_radiation_w_m2", -1.0),
        ("temp_c", float("nan")),
    ],
)
def test_calculate_wbgt_rejects_invalid_inputs(
    input_name: str,
    input_value: float,
) -> None:
    """Out-of-range and non-finite input values are reported."""
    conditions = {
        "temp_c": 30.0,
        "relative_humidity_pct": 50.0,
        "wind_speed_m_s": 1.0,
        "solar_radiation_w_m2": 500.0,
    }
    conditions[input_name] = input_value

    with pytest.raises(ValueError):
        calculate_wbgt(**conditions)
