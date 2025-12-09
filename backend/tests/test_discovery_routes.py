import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_baseline_endpoint(client: TestClient):
    resp = client.get(
        "/api/v1/data/baseline",
        params={"start_date": "2024-10-01", "end_date": "2024-10-07"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sales"] > 0
    assert data["total_margin"] > 0
    assert data["total_units"] > 0
    assert len(data["daily_projections"]) == 7


def test_discovery_opportunities(client: TestClient):
    resp = client.get("/api/v1/discovery/opportunities", params={"month": "2024-10", "geo": "DE"})
    assert resp.status_code == 200
    opportunities = resp.json()
    assert isinstance(opportunities, list)
    assert len(opportunities) > 0
    # Ensure they are sorted by estimated_potential descending
    potentials = [item["estimated_potential"] for item in opportunities]
    assert potentials == sorted(potentials, reverse=True)


def test_discovery_gaps(client: TestClient):
    resp = client.get("/api/v1/discovery/gaps", params={"month": "2024-10", "geo": "DE"})
    assert resp.status_code == 200
    gaps = resp.json()
    assert "sales_gap" in gaps
    assert "margin_gap" in gaps
    assert "units_gap" in gaps
