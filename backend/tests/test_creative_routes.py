import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_generate_brief(client: TestClient):
    """Test creative brief generation."""
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
    
    response = client.post(
        "/api/v1/creative/brief",
        json={
            "scenario": scenario,
            "segments": None
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "scenario_id" in data
    assert "objectives" in data
    assert "messaging" in data
    assert "tone" in data
    assert "style" in data


def test_generate_assets(client: TestClient):
    """Test asset specification generation."""
    brief = {
        "scenario_id": "test-scenario-1",
        "objectives": ["Drive sales", "Increase awareness"],
        "messaging": "Test promotional message",
        "target_audience": "General consumers",
        "tone": "confident",
        "style": "benefit-led",
        "mandatory_elements": ["Discount: 15%", "Departments: TV"]
    }
    
    response = client.post("/api/v1/creative/assets", json=brief)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "asset_type" in data[0]
    assert "copy_text" in data[0]


def test_finalize_campaign(client: TestClient):
    """Test campaign finalization."""
    scenarios = [
        {
            "id": "scenario-1",
            "name": "Test Scenario",
            "date_range": {
                "start_date": "2024-10-01",
                "end_date": "2024-10-07"
            },
            "departments": ["TV"],
            "channels": ["online"],
            "discount_percentage": 15.0
        }
    ]
    
    response = client.post("/api/v1/creative/finalize", json=scenarios)
    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data
    assert "timeline" in data
    assert "execution_details" in data
