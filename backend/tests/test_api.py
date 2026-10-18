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


def test_frontend_risk_profile_alias_is_accepted() -> None:
    response = client.get(
        "/api/risk",
        params={
            "lat": 28.743,
            "lon": 77.081,
            "activity": "outdoor_work",
            "duration_min": 240,
            "profile": "worker",
        },
    )
    assert response.status_code == 200
    assert response.json()["risk_score"] > 0


def test_heatmap_returns_geojson_and_validates_bbox() -> None:
    response = client.get("/api/heatmap", params={"bbox": "77.04,28.70,77.14,28.78"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) == 4
    assert payload["features"][0]["properties"]["population_exposed"] > 0
    assert payload["features"][0]["geometry"]["type"] == "Point"
    assert len(payload["features"][0]["geometry"]["coordinates"]) == 2
    assert client.get("/api/heatmap", params={"bbox": "bad"}).status_code == 422
    frontend_query = client.get(
        "/api/heatmap",
        params={"bbox": "77.02,28.69,77.13,28.79", "ts": "latest"},
    )
    assert frontend_query.status_code == 200


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


def test_route_detour_remains_in_wgs84_at_coordinate_limits() -> None:
    for latitude, longitude in ((90, 180), (-90, -180)):
        response = client.post(
            "/api/route",
            json={
                "origin": {"lat": latitude, "lon": longitude},
                "dest": {"lat": latitude, "lon": longitude},
                "activity": "walking",
            },
        )
        assert response.status_code == 200
        coordinates = response.json()["coolest"]["geometry"]["coordinates"]
        assert all(-180 <= point[0] <= 180 and -90 <= point[1] <= 90 for point in coordinates)


def test_optimization_and_simulation_validate_and_return_results() -> None:
    optimized = client.post(
        "/api/optimize",
        json={"budget_inr": 60_000, "bbox": [77.04, 28.70, 77.14, 28.78]},
    )
    assert optimized.status_code == 200
    assert optimized.json()["total_cost_inr"] <= 60_000
    assert optimized.json()["ranked_hotspots"]
    assert optimized.json()["budget_inr"] == 60_000
    assert optimized.json()["interventions"]
    assert client.post(
        "/api/optimize", json={"budget_inr": -1, "bbox": [77.14, 28.78, 77.04, 28.70]}
    ).status_code == 422

    baseline = client.get("/api/heatmap", params={"bbox": "77.04,28.70,77.14,28.78"}).json()
    simulated = client.post(
        "/api/simulate",
        json={
            "interventions": [
                {"cell_id": baseline["features"][3]["properties"]["cell_id"], "type": "shade", "units": 1}
            ]
        },
    )
    assert simulated.status_code == 200
    baseline_risk = baseline["features"][3]["properties"]["risk"]
    simulated_risk = simulated.json()["features"][3]["properties"]["risk"]
    assert simulated_risk < baseline_risk
    assert client.post(
        "/api/simulate",
        json={"interventions": [{"cell_id": "not-a-cell", "type": "shade", "units": 1}]},
    ).status_code == 422
    assert client.post(
        "/api/simulate", json={"interventions": [{"type": "shade", "units": 1}]}
    ).status_code == 422


def test_simulation_uses_source_bbox_and_rejects_mixed_bboxes() -> None:
    first_bbox = "77.02,28.69,77.13,28.79"
    second_bbox = "76.20,28.50,76.40,28.70"
    first_heatmap = client.get("/api/heatmap", params={"bbox": first_bbox}).json()
    second_heatmap = client.get("/api/heatmap", params={"bbox": second_bbox}).json()
    first_plan = client.post(
        "/api/optimize",
        json={"budget_inr": 250_000, "bbox": [77.02, 28.69, 77.13, 28.79]},
    ).json()
    selected_cell_id = first_plan["ranked_hotspots"][0]["cell_id"]
    first_cell = next(
        item for item in first_heatmap["features"] if item["properties"]["cell_id"] == selected_cell_id
    )
    second_cell = second_heatmap["features"][0]

    assert first_cell["properties"]["cell_id"] != second_cell["properties"]["cell_id"]
    simulated = client.post(
        "/api/simulate",
        json={
            "interventions": [
                {"cell_id": selected_cell_id, "type": "shade", "units": 1}
            ]
        },
    )
    assert simulated.status_code == 200
    simulated_features = simulated.json()["features"]
    assert [item["geometry"] for item in simulated_features] == [item["geometry"] for item in first_heatmap["features"]]
    assert simulated_features[0]["properties"]["risk"] < first_cell["properties"]["risk"]

    mixed = client.post(
        "/api/simulate",
        json={
            "interventions": [
                {"cell_id": selected_cell_id, "type": "shade"},
                {"cell_id": second_cell["properties"]["cell_id"], "type": "water"},
            ]
        },
    )
    assert mixed.status_code == 422


def test_frontend_optimizer_path_and_string_bbox_are_accepted() -> None:
    response = client.post(
        "/api/interventions/optimize",
        json={"bbox": "77.02,28.69,77.13,28.79", "budget_inr": 250_000},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["budget_inr"] == 250_000
    assert payload["population_exposed"] > 0
    assert payload["people_reached"] > 0
    assert all({"name", "locations", "cost_inr"} <= item.keys() for item in payload["interventions"])


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