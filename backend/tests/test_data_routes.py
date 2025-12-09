import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_get_baseline(client: TestClient):
    """Test baseline forecast endpoint."""
    response = client.get(
        "/api/v1/data/baseline",
        params={
            "start_date": "2024-10-01",
            "end_date": "2024-10-07"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_sales" in data
    assert "total_margin" in data
    assert "total_units" in data
    assert "daily_projections" in data
    assert data["total_sales"] > 0


def test_get_quality_report(client: TestClient):
    """Test data quality report endpoint."""
    response = client.get(
        "/api/v1/data/quality",
        params={"dataset_id": "test-dataset"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "completeness" in data
    assert "accuracy" in data
    assert "consistency" in data
    assert "timeliness" in data
    assert "issues" in data
    assert "recommendations" in data
