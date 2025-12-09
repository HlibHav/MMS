import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta

from api.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_create_scenario(client: TestClient):
    """Test scenario creation endpoint."""
    response = client.post(
        "/api/v1/scenarios/create",
        json={
            "brief": {
                "month": "2024-10",
                "promo_date_range": {"start": "2024-10-01", "end": "2024-10-07"},
                "focus_departments": ["TV", "Gaming"],
                "objectives": {"geo": "DE"},
                "constraints": {"max_discount_pct": 25}
            },
            "scenario_type": "balanced",
            "parameters": {
                "name": "Test Scenario",
                "discount_percentage": 15.0
            },
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "scenario" in data
    assert data["scenario"]["name"] == "Test Scenario"
    assert "kpi" in data
    assert "validation" in data


def test_evaluate_scenario(client: TestClient):
    """Test scenario evaluation endpoint."""
    scenario = {
        "id": "test-scenario-1",
        "name": "Test Scenario",
        "date_range": {
            "start_date": "2024-10-01",
            "end_date": "2024-10-07"
        },
        "departments": ["TV"],
        "channels": ["online"],
        "discount_percentage": 15.0
    }
    
    response = client.post("/api/v1/scenarios/evaluate", json=scenario)
    assert response.status_code == 200
    data = response.json()
    assert "kpi" in data
    assert data["kpi"]["total_sales"] > 0


def test_validate_scenario(client: TestClient):
    """Test scenario validation endpoint."""
    scenario = {
        "id": "test-scenario-1",
        "name": "Test Scenario",
        "date_range": {
            "start_date": "2024-10-01",
            "end_date": "2024-10-07"
        },
        "departments": ["TV"],
        "channels": ["online"],
        "discount_percentage": 15.0
    }
    
    response = client.post("/api/v1/scenarios/validate", json=scenario)
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "issues" in data
    assert "checks_passed" in data


def test_compare_scenarios(client: TestClient):
    """Test scenario comparison endpoint."""
    scenarios = [
        {
            "id": "scenario-1",
            "name": "Conservative",
            "date_range": {
                "start_date": "2024-10-01",
                "end_date": "2024-10-07"
            },
            "departments": ["TV"],
            "channels": ["online"],
            "discount_percentage": 10.0
        },
        {
            "id": "scenario-2",
            "name": "Aggressive",
            "date_range": {
                "start_date": "2024-10-01",
                "end_date": "2024-10-07"
            },
            "departments": ["TV"],
            "channels": ["online"],
            "discount_percentage": 20.0
        }
    ]
    
    response = client.post("/api/v1/scenarios/compare", json=scenarios)
    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data
    assert "kpis" in data
    assert "comparison_table" in data
    assert len(data["kpis"]) == 2
