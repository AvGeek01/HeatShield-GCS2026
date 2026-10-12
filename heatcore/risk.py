"""Personal heat-risk assessment interface."""

from collections.abc import Mapping
from typing import Literal, TypedDict

RiskLevel = Literal["low", "moderate", "high", "extreme"]


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
    """Assess personal heat risk and return the ``/api/risk`` response fields.

    Args:
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.
        activity: Planned activity used to estimate heat exposure.
        duration_min: Planned activity duration in minutes.
        profile: User profile used to personalize risk and recommendations.
        weather: Forecast weather values for the location and assessment time.

    Returns:
        A mapping containing ``risk_score`` (0–100), ``level``, ``wbgt_c``,
        explanatory ``factors``, and recommended ``actions``.
    """
    raise NotImplementedError
