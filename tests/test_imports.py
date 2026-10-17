"""Smoke tests for the heatcore public module surface."""

import pytest

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


def test_heatmap_cell_fields_match_api() -> None:
    """Heatmap cells expose the fields documented by ``/api/heatmap``."""
    assert set(optimizer.HeatmapCell.__annotations__) == {
        "risk",
        "temp_c",
        "wbgt_c",
        "population_exposed",
    }


def test_scaffold_functions_raise_not_implemented() -> None:
    """Public scaffold functions clearly signal that algorithms are pending."""
    with pytest.raises(NotImplementedError):
        features.build_feature_vector(
            lat=28.7,
            lon=77.1,
            activity="walking",
            duration_min=30,
            profile="default",
            weather={},
        )
    with pytest.raises(NotImplementedError):
        wbgt.calculate_wbgt(
            temp_c=35.0,
            relative_humidity_pct=50.0,
            wind_speed_m_s=1.0,
            solar_radiation_w_m2=500.0,
        )
    with pytest.raises(NotImplementedError):
        model.predict_risk({})
    with pytest.raises(NotImplementedError):
        risk.assess_risk(
            lat=28.7,
            lon=77.1,
            activity="walking",
            duration_min=30,
            profile="default",
            weather={},
        )
    with pytest.raises(NotImplementedError):
        routing.find_heat_aware_route(
            start=(28.7, 77.1),
            destination=(28.8, 77.2),
        )
    with pytest.raises(NotImplementedError):
        optimizer.optimize_interventions(
            [],
            budget=1000.0,
            cost_per_cell=100.0,
        )
