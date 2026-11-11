"""Tests for personalized heat-risk scoring and factor explanations."""

import pytest

from heatcore.risk import RiskResponse, assess_risk, get_top_risk_factors
from heatcore.wbgt import calculate_wbgt


def _assess(
    *,
    wbgt_c: float,
    activity: str = "walking",
    duration_min: int = 60,
    profile: str = "general",
) -> RiskResponse:
    """Assess one direct-WBGT scenario with the pilot's DTU-area location."""
    return assess_risk(
        lat=28.75,
        lon=77.12,
        activity=activity,
        duration_min=duration_min,
        profile=profile,
        weather={"wbgt_c": wbgt_c},
    )


@pytest.mark.parametrize(
    ("wbgt_c", "expected_level"),
    [
        (20.0, "low"),
        (26.0, "moderate"),
        (29.0, "high"),
        (32.0, "extreme"),
    ],
)
def test_wbgt_screening_anchors_set_risk_levels(
    wbgt_c: float,
    expected_level: str,
) -> None:
    """Named WBGT anchors map to the corresponding risk band."""
    result = _assess(wbgt_c=wbgt_c)

    assert result["level"] == expected_level


def test_risk_score_is_bounded_and_increases_with_heat() -> None:
    """Increasing WBGT increases a score that remains within 0–100."""
    cool_result = _assess(wbgt_c=22.0)
    hot_result = _assess(wbgt_c=33.0)

    assert 0.0 <= cool_result["risk_score"] <= 100.0
    assert 0.0 <= hot_result["risk_score"] <= 100.0
    assert hot_result["risk_score"] > cool_result["risk_score"]


@pytest.mark.parametrize(
    ("field", "higher_value"),
    [
        ("activity", "running"),
        ("duration_min", 120),
        ("profile", "chronic_condition"),
    ],
)
def test_exertion_duration_and_vulnerability_raise_score(
    field: str,
    higher_value: str | int,
) -> None:
    """More strenuous activity, longer exposure, and vulnerability raise risk."""
    baseline = _assess(wbgt_c=30.0)
    adjusted = _assess(wbgt_c=30.0, **{field: higher_value})

    assert adjusted["risk_score"] > baseline["risk_score"]


def test_weather_inputs_are_converted_to_wbgt() -> None:
    """Meteorological inputs use the shared WBGT calculation."""
    weather = {
        "temp_c": 35.0,
        "relative_humidity_pct": 55.0,
        "wind_speed_m_s": 1.0,
        "solar_radiation_w_m2": 600.0,
    }

    result = assess_risk(
        lat=28.75,
        lon=77.12,
        activity="walking",
        duration_min=60,
        profile="general",
        weather=weather,
    )

    assert result["wbgt_c"] == pytest.approx(
        calculate_wbgt(
            temp_c=weather["temp_c"],
            relative_humidity_pct=weather["relative_humidity_pct"],
            wind_speed_m_s=weather["wind_speed_m_s"],
            solar_radiation_w_m2=weather["solar_radiation_w_m2"],
        )
    )


def test_response_has_plain_english_factors_and_actions() -> None:
    """Risk responses include readable drivers and non-empty recommended actions."""
    result = _assess(
        wbgt_c=31.0,
        activity="outdoor_work",
        duration_min=120,
        profile="older_adult",
    )

    assert 1 <= len(result["factors"]) <= 3
    assert all(isinstance(factor, str) and factor for factor in result["factors"])
    assert result["actions"]


def test_worker_profile_alias_matches_outdoor_worker() -> None:
    """The API's legacy ``worker`` profile uses the outdoor-worker multiplier."""
    worker = _assess(wbgt_c=30.0, profile="worker")
    outdoor_worker = _assess(wbgt_c=30.0, profile="outdoor_worker")

    assert worker == outdoor_worker


def test_factor_function_respects_requested_limit() -> None:
    """The public factor helper returns no more than the requested count."""
    factors = get_top_risk_factors(
        wbgt_c=32.0,
        activity="running",
        duration_min=120,
        profile="chronic_condition",
        top_n=2,
    )

    assert len(factors) == 2
    assert all(isinstance(factor, str) for factor in factors)


@pytest.mark.parametrize(
    ("overrides", "weather"),
    [
        ({"activity": "swimming"}, {"wbgt_c": 30.0}),
        ({"duration_min": 0}, {"wbgt_c": 30.0}),
        ({"profile": "unknown"}, {"wbgt_c": 30.0}),
        ({}, {"temp_c": 30.0}),
        ({}, {"wbgt_c": float("nan")}),
    ],
)
def test_assess_risk_rejects_invalid_inputs(
    overrides: dict[str, str | int],
    weather: dict[str, float],
) -> None:
    """Unsupported exposure data and incomplete weather fail explicitly."""
    activity = str(overrides.get("activity", "walking"))
    duration_min = int(overrides.get("duration_min", 60))
    profile = str(overrides.get("profile", "general"))

    with pytest.raises(ValueError):
        assess_risk(
            lat=28.75,
            lon=77.12,
            activity=activity,
            duration_min=duration_min,
            profile=profile,
            weather=weather,
        )


def test_factor_function_rejects_non_positive_top_n() -> None:
    """A factor count below one is invalid."""
    with pytest.raises(ValueError, match="top_n"):
        get_top_risk_factors(
            wbgt_c=30.0,
            activity="walking",
            duration_min=60,
            profile="general",
            top_n=0,
        )
