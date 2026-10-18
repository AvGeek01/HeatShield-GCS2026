from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_openapi_lists_all_requested_endpoints() -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) >= {
        "/api/risk",
        "/api/heatmap",
        "/api/route",
        "/api/resources",
        "/api/optimize",
        "/api/simulate",
        "/api/readings",
    }


def test_risk_is_bounded_and_has_recommendations() -> None:
    response = client.get(
        "/api/risk",
        params={"lat": 28.75, "lon": 77.1, "activity": "walking", "duration_min": 30, "profile": "general"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert 0 <= payload["risk_score"] <= 100
    assert payload["level"] in {"low", "moderate", "high", "extreme"}
    assert payload["actions"]


def test_heatmap_returns_geojson_and_validates_bbox() -> None:
    response = client.get("/api/heatmap", params={"bbox": "77.04,28.70,77.14,28.78"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) == 4
    assert payload["features"][0]["properties"]["population_exposed"] > 0
    assert client.get("/api/heatmap", params={"bbox": "bad"}).status_code == 422


def test_route_and_resources_return_expected_shapes() -> None:
    route = client.post(
        "/api/route",
        json={"origin": {"lat": 28.74, "lon": 77.1}, "dest": {"lat": 28.76, "lon": 77.12}, "activity": "walking"},
    )
    assert route.status_code == 200
    assert route.json()["fastest"]["duration_min"] <= route.json()["coolest"]["duration_min"]
    resources = client.get(
        "/api/resources", params={"type": "water", "lat": 28.75, "lon": 77.1, "radius_m": 2_000}
    )
    assert resources.status_code == 200
    assert all(item["type"] == "water" for item in resources.json()["resources"])


def test_optimization_and_simulation_validate_and_return_results() -> None:
    optimized = client.post(
        "/api/optimize",
        json={"budget_inr": 60_000, "bbox": [77.04, 28.70, 77.14, 28.78]},
    )
    assert optimized.status_code == 200
    assert optimized.json()["total_cost_inr"] <= 60_000
    assert optimized.json()["ranked_hotspots"]
    assert client.post(
        "/api/optimize", json={"budget_inr": -1, "bbox": [77.14, 28.78, 77.04, 28.70]}
    ).status_code == 422

    baseline = client.get("/api/heatmap", params={"bbox": "77.04,28.70,77.14,28.78"}).json()
    simulated = client.post(
        "/api/simulate",
        json={"interventions": [{"cell_id": "delhi-1-1", "type": "shade", "units": 1}]},
    )
    assert simulated.status_code == 200
    baseline_risk = baseline["features"][3]["properties"]["risk"]
    simulated_risk = simulated.json()["features"][3]["properties"]["risk"]
    assert simulated_risk < baseline_risk


def test_reading_is_accepted_and_input_is_validated() -> None:
    reading = {
        "node_id": "dtu-node-01",
        "ts": "2026-10-18T12:00:00Z",
        "temp_c": 36.2,
        "rh": 42,
        "lux": 18_000,
        "lat": 28.75,
        "lon": 77.1,
    }
    response = client.post("/api/readings", json=reading)
    assert response.status_code == 202
    assert response.json()["accepted"] is True
    assert client.post("/api/readings", json={**reading, "temp_c": 200}).status_code == 422


def test_cors_and_swagger_are_enabled() -> None:
    assert client.get("/docs").status_code == 200
    response = client.options(
        "/api/risk",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"