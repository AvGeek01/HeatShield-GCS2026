"""Heat-aware routing interfaces."""

from collections.abc import Sequence
from typing import TypedDict


class RouteResult(TypedDict):
    """Result shape for a heat-aware route lookup."""

    coordinates: list[tuple[float, float]]
    distance_m: float
    risk_score: float


def find_heat_aware_route(
    *,
    start: tuple[float, float],
    destination: tuple[float, float],
    avoid_hotspots: Sequence[dict[str, object]] = (),
) -> RouteResult:
    """Find a route that accounts for heat exposure and hotspot locations.

    Coordinates are expressed as ``(latitude, longitude)`` pairs. Hotspot
    inputs may be derived from the ``/api/heatmap`` GeoJSON cell collection.

    Returns:
        Route coordinates, route distance in metres, and an aggregate
        0–100 heat-risk score.
    """
    raise NotImplementedError
