"""Model interface for translating heat exposure features into risk scores."""

from collections.abc import Mapping

from heatcore.features import FeatureValue

RISK_SCORE_MIN = 0.0
RISK_SCORE_MAX = 100.0


def predict_risk(features: Mapping[str, FeatureValue]) -> float:
    """Predict a personal heat-risk score on a 0–100 scale.

    Args:
        features: Feature mapping prepared for the configured model.

    Returns:
        A risk score between 0 (lowest risk) and 100 (highest risk).
    """
    raise NotImplementedError
