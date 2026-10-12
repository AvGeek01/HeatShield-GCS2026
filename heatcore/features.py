"""Feature preparation for personal heat-risk predictions."""

from collections.abc import Mapping
from datetime import datetime

FeatureValue = float | str


def build_feature_vector(
    *,
    lat: float,
    lon: float,
    activity: str,
    duration_min: int,
    profile: str,
    weather: Mapping[str, float],
    timestamp: datetime | None = None,
) -> dict[str, FeatureValue]:
    """Build model features from location, activity, profile, and weather inputs.

    The returned mapping is intended for the risk model. Weather values are
    supplied by the caller; the required weather keys and feature encoding
    will be defined with the selected forecast and training data.
    """
    raise NotImplementedError
