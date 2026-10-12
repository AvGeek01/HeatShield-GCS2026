"""Smoke tests for the heatcore public module surface."""

import heatcore
from heatcore import features, model, optimizer, risk, routing, wbgt


def test_package_and_modules_import() -> None:
    """All planned core modules are importable."""
    assert heatcore.assess_risk is risk.assess_risk
    assert callable(features.build_feature_vector)
    assert callable(wbgt.calculate_wbgt)
    assert callable(model.predict_risk)
    assert callable(routing.find_heat_aware_route)
    assert callable(optimizer.optimize_interventions)


def test_risk_response_fields_match_api() -> None:
    """The risk result type declares all documented API response fields."""
    assert set(risk.RiskResponse.__annotations__) == {
        "risk_score",
        "level",
        "wbgt_c",
        "factors",
        "actions",
    }
