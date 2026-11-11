"""Explainable personal heat-risk scoring for the HeatShield pilot."""

import math
from collections.abc import Mapping
from typing import Literal, TypedDict

from heatcore.wbgt import WBGT_MAX_C, WBGT_MIN_C, calculate_wbgt

RiskLevel = Literal["low", "moderate", "high", "extreme"]

RISK_SCORE_MIN = 0.0
RISK_SCORE_MAX = 100.0
MODERATE_SCORE_THRESHOLD = 25.0
HIGH_SCORE_THRESHOLD = 50.0
EXTREME_SCORE_THRESHOLD = 75.0

# Illustrative screening anchors inspired by ISO 7243 / ACGIH heat-stress
# guidance. They are proposal values, not regulatory exposure limits; actual
# limits depend on workload, acclimatization, clothing, and local conditions.
WBGT_REFERENCE_C = 20.0
WBGT_MODERATE_THRESHOLD_C = 26.0
WBGT_HIGH_THRESHOLD_C = 29.0
WBGT_EXTREME_THRESHOLD_C = 32.0
WBGT_SCORE_CEILING_C = 35.0
WBGT_SCORE_ANCHORS: tuple[tuple[float, float], ...] = (
    (WBGT_REFERENCE_C, RISK_SCORE_MIN),
    (WBGT_MODERATE_THRESHOLD_C, MODERATE_SCORE_THRESHOLD),
    (WBGT_HIGH_THRESHOLD_C, HIGH_SCORE_THRESHOLD),
    (WBGT_EXTREME_THRESHOLD_C, EXTREME_SCORE_THRESHOLD),
    (WBGT_SCORE_CEILING_C, RISK_SCORE_MAX),
)

REFERENCE_ACTIVITY_MET = 3.0
REFERENCE_DURATION_MIN = 60
MAX_DURATION_MIN = 720
MIN_COORDINATE_LAT = -90.0
MAX_COORDINATE_LAT = 90.0
MIN_COORDINATE_LON = -180.0
MAX_COORDINATE_LON = 180.0
FACTOR_SIGNIFICANCE_POINTS = 0.5

# Representative activity MET values, normalized against a moderate 3-MET
# activity. They are coarse planning assumptions, not personal measurements.
ACTIVITY_MET_VALUES: dict[str, float] = {
    "resting": 1.0,
    "walking": 3.0,
    "commuting": 3.0,
    "cycling": 6.0,
    "running": 8.0,
    "outdoor_work": 4.0,
}

PROFILE_VULNERABILITY_MULTIPLIERS: dict[str, float] = {
    "general": 1.0,
    "child": 1.15,
    "older_adult": 1.2,
    "outdoor_worker": 1.1,
    "chronic_condition": 1.25,
}
PROFILE_ALIASES = {"worker": "outdoor_worker"}

LOW_RISK_ACTIONS = ["Stay hydrated", "Take breaks if conditions change"]
MODERATE_RISK_ACTIONS = [
    "Prefer shade and water breaks",
    "Reduce or reschedule strenuous outdoor activity",
]
HIGH_RISK_ACTIONS = [
    "Avoid strenuous outdoor activity during the hottest hours",
    "Take frequent shaded breaks and drink water",
]
EXTREME_RISK_ACTIONS = [
    "Avoid outdoor exertion and move to a cool indoor place",
    "Follow local heat-health guidance; seek help for heat-illness symptoms",
]


class RiskResponse(TypedDict):
    """Response shape for ``GET /api/risk``."""

    risk_score: float
    level: RiskLevel
    wbgt_c: float
    factors: list[str]
    actions: list[str]


def assess_risk(
    *,
    lat: float,
    lon: float,
    activity: str,
    duration_min: int,
    profile: str,
    weather: Mapping[str, float],
) -> RiskResponse:
    """Estimate a 0–100 personal heat-risk score and explain its drivers.

    ``weather`` may provide ``wbgt_c`` directly or the four inputs accepted by
    :func:`heatcore.wbgt.calculate_wbgt`: ``temp_c``,
    ``relative_humidity_pct``, ``wind_speed_m_s``, and
    ``solar_radiation_w_m2``. The score interpolates illustrative WBGT
    screening anchors, then multiplies by the square roots of activity MET
    relative to 3 MET and duration relative to 60 minutes, and by the profile
    vulnerability multiplier. The result is clipped to 0–100. These are
    proposal assumptions, not a diagnosis or a standards-compliance
    determination.

    Args:
        lat: Latitude in decimal degrees, used to validate the request location.
        lon: Longitude in decimal degrees, used to validate the request location.
        activity: One of the activities in :data:`ACTIVITY_MET_VALUES`.
        duration_min: Planned exposure duration, from 1 to 720 minutes.
        profile: One of the profiles in :data:`PROFILE_VULNERABILITY_MULTIPLIERS`.
            ``worker`` is accepted as an alias for ``outdoor_worker``.
        weather: WBGT or meteorological weather inputs.

    Returns:
        A mapping with ``risk_score``, ``level``, ``wbgt_c``, plain-English
        ``factors``, and recommended ``actions``.

    Raises:
        ValueError: If a location, activity, profile, duration, or weather
            input is invalid or missing.
    """
    _validate_coordinate(lat, "lat", MIN_COORDINATE_LAT, MAX_COORDINATE_LAT)
    _validate_coordinate(lon, "lon", MIN_COORDINATE_LON, MAX_COORDINATE_LON)
    _validate_exposure(activity, duration_min, profile)

    wbgt_c = _get_wbgt_c(weather)
    risk_score = _calculate_risk_score(wbgt_c, activity, duration_min, profile)
    level = _get_risk_level(risk_score)
    return {
        "risk_score": risk_score,
        "level": level,
        "wbgt_c": wbgt_c,
        "factors": get_top_risk_factors(
            wbgt_c=wbgt_c,
            activity=activity,
            duration_min=duration_min,
            profile=profile,
        ),
        "actions": _actions_for_level(level),
    }


def get_top_risk_factors(
    *,
    wbgt_c: float,
    activity: str,
    duration_min: int,
    profile: str,
    top_n: int = 3,
) -> list[str]:
    """Return up to ``top_n`` human-readable score contributors.

    Contributions are compared against a 3-MET activity, one hour of
    exposure, and the general profile. Negative contributions are reported as
    risk reductions so the factors explain both hazards and mitigators.

    Args:
        wbgt_c: Wet-bulb globe temperature in degrees Celsius.
        activity: One of the activities in :data:`ACTIVITY_MET_VALUES`.
        duration_min: Planned exposure duration, from 1 to 720 minutes.
        profile: One of the supported vulnerability profiles.
        top_n: Maximum number of contributing factors to return.

    Returns:
        Plain-English factors sorted by absolute modeled score contribution.

    Raises:
        ValueError: If an input or ``top_n`` is invalid.
    """
    _validate_wbgt(wbgt_c)
    _validate_exposure(activity, duration_min, profile)
    if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n < 1:
        raise ValueError("top_n must be a positive integer")

    canonical_profile = PROFILE_ALIASES.get(profile, profile)
    thermal_score = _thermal_score(wbgt_c)
    activity_met = ACTIVITY_MET_VALUES[activity]
    activity_multiplier = math.sqrt(activity_met / REFERENCE_ACTIVITY_MET)
    duration_multiplier = math.sqrt(duration_min / REFERENCE_DURATION_MIN)
    profile_multiplier = PROFILE_VULNERABILITY_MULTIPLIERS[canonical_profile]

    contributions = [
        (
            thermal_score,
            (
                f"WBGT of {wbgt_c:.1f}°C contributes "
                f"{thermal_score:.0f} baseline heat-risk points."
            ),
        ),
        (
            thermal_score * (activity_multiplier - 1.0),
            _adjustment_factor(
                f"{activity.replace('_', ' ')} activity (~{activity_met:g} MET)",
                thermal_score * (activity_multiplier - 1.0),
            ),
        ),
        (
            thermal_score
            * activity_multiplier
            * (duration_multiplier - 1.0),
            _adjustment_factor(
                f"{duration_min} minutes of exposure",
                thermal_score
                * activity_multiplier
                * (duration_multiplier - 1.0),
            ),
        ),
        (
            thermal_score
            * activity_multiplier
            * duration_multiplier
            * (profile_multiplier - 1.0),
            _adjustment_factor(
                f"the {canonical_profile.replace('_', ' ')} profile",
                thermal_score
                * activity_multiplier
                * duration_multiplier
                * (profile_multiplier - 1.0),
            ),
        ),
    ]
    contributions.sort(key=lambda item: abs(item[0]), reverse=True)

    factors = [
        description
        for contribution, description in contributions
        if abs(contribution) >= FACTOR_SIGNIFICANCE_POINTS
    ]
    if not factors:
        factors.append(
            f"WBGT of {wbgt_c:.1f}°C is below the "
            f"{WBGT_REFERENCE_C:.0f}°C reference for modeled heat loading."
        )
    return factors[:top_n]


def _validate_coordinate(
    value: float,
    name: str,
    minimum: float,
    maximum: float,
) -> None:
    """Validate a finite coordinate value against its geographic range."""
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")


def _validate_exposure(activity: str, duration_min: int, profile: str) -> None:
    """Validate activity, duration, and vulnerability profile values."""
    if activity not in ACTIVITY_MET_VALUES:
        supported = ", ".join(sorted(ACTIVITY_MET_VALUES))
        raise ValueError(f"activity must be one of: {supported}")
    if (
        isinstance(duration_min, bool)
        or not isinstance(duration_min, int)
        or not 1 <= duration_min <= MAX_DURATION_MIN
    ):
        raise ValueError(f"duration_min must be between 1 and {MAX_DURATION_MIN}")
    canonical_profile = PROFILE_ALIASES.get(profile, profile)
    if canonical_profile not in PROFILE_VULNERABILITY_MULTIPLIERS:
        supported = ", ".join(sorted(PROFILE_VULNERABILITY_MULTIPLIERS))
        raise ValueError(f"profile must be one of: {supported}")


def _get_wbgt_c(weather: Mapping[str, float]) -> float:
    """Return supplied WBGT or calculate it from required weather variables."""
    if "wbgt_c" in weather:
        wbgt_c = _finite_weather_value(weather, "wbgt_c")
        _validate_wbgt(wbgt_c)
        return wbgt_c

    weather_keys = (
        "temp_c",
        "relative_humidity_pct",
        "wind_speed_m_s",
        "solar_radiation_w_m2",
    )
    missing_keys = [key for key in weather_keys if key not in weather]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ValueError(
            f"weather must include wbgt_c or all meteorological inputs; missing: {missing}"
        )
    return calculate_wbgt(
        temp_c=_finite_weather_value(weather, "temp_c"),
        relative_humidity_pct=_finite_weather_value(
            weather,
            "relative_humidity_pct",
        ),
        wind_speed_m_s=_finite_weather_value(weather, "wind_speed_m_s"),
        solar_radiation_w_m2=_finite_weather_value(
            weather,
            "solar_radiation_w_m2",
        ),
    )


def _finite_weather_value(weather: Mapping[str, float], name: str) -> float:
    """Return one weather value as a finite float or report invalid input."""
    value = weather[name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"weather[{name!r}] must be a finite number")
    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        raise ValueError(f"weather[{name!r}] must be a finite number")
    return numeric_value


def _validate_wbgt(wbgt_c: float) -> None:
    """Validate WBGT as a finite value within the calculator's supported range."""
    if not math.isfinite(wbgt_c) or not WBGT_MIN_C <= wbgt_c <= WBGT_MAX_C:
        raise ValueError(f"wbgt_c must be between {WBGT_MIN_C} and {WBGT_MAX_C}")


def _thermal_score(wbgt_c: float) -> float:
    """Interpolate the named pilot WBGT anchors to a 0–100 score."""
    if wbgt_c <= WBGT_REFERENCE_C:
        return RISK_SCORE_MIN
    if wbgt_c >= WBGT_SCORE_CEILING_C:
        return RISK_SCORE_MAX
    for (lower_wbgt, lower_score), (upper_wbgt, upper_score) in zip(
        WBGT_SCORE_ANCHORS,
        WBGT_SCORE_ANCHORS[1:],
    ):
        if wbgt_c <= upper_wbgt:
            fraction = (wbgt_c - lower_wbgt) / (upper_wbgt - lower_wbgt)
            return lower_score + fraction * (upper_score - lower_score)
    return RISK_SCORE_MAX


def _calculate_risk_score(
    wbgt_c: float,
    activity: str,
    duration_min: int,
    profile: str,
) -> float:
    """Combine thermal severity with exertion, duration, and vulnerability."""
    canonical_profile = PROFILE_ALIASES.get(profile, profile)
    activity_multiplier = math.sqrt(
        ACTIVITY_MET_VALUES[activity] / REFERENCE_ACTIVITY_MET
    )
    duration_multiplier = math.sqrt(duration_min / REFERENCE_DURATION_MIN)
    profile_multiplier = PROFILE_VULNERABILITY_MULTIPLIERS[canonical_profile]
    score = _thermal_score(wbgt_c) * activity_multiplier
    score *= duration_multiplier * profile_multiplier
    return min(RISK_SCORE_MAX, max(RISK_SCORE_MIN, score))


def _get_risk_level(risk_score: float) -> RiskLevel:
    """Map the bounded score to the pilot's named risk bands."""
    if risk_score >= EXTREME_SCORE_THRESHOLD:
        return "extreme"
    if risk_score >= HIGH_SCORE_THRESHOLD:
        return "high"
    if risk_score >= MODERATE_SCORE_THRESHOLD:
        return "moderate"
    return "low"


def _actions_for_level(level: RiskLevel) -> list[str]:
    """Return the standard action prompts for a risk band."""
    if level == "extreme":
        return EXTREME_RISK_ACTIONS.copy()
    if level == "high":
        return HIGH_RISK_ACTIONS.copy()
    if level == "moderate":
        return MODERATE_RISK_ACTIONS.copy()
    return LOW_RISK_ACTIONS.copy()


def _adjustment_factor(label: str, contribution: float) -> str:
    """Describe an exposure adjustment in plain English."""
    direction = "raises" if contribution >= 0.0 else "reduces"
    return (
        f"{label.capitalize()} {direction} modeled risk by "
        f"{abs(contribution):.0f} points versus the reference exposure."
    )
