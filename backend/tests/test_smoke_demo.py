import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_discovery_opportunities(client: TestClient):
    resp = client.get("/api/v1/discovery/opportunities", params={"month": "2024-10", "geo": "DE"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data, "expected at least one opportunity"
    assert "department" in data[0]


def test_optimization_generate(client: TestClient):
    payload = {
        "brief": "Find October promos for electronics",
        "constraints": {"objectives": {"sales": 0.6, "margin": 0.4}},
        "num_scenarios": 2,
    }
    resp = client.post("/api/v1/optimization/generate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "scenarios" in body
    assert body["scenarios"], "expected optimized scenarios"
    first = body["scenarios"][0]
    assert "scenario" in first and "kpi" in first


def test_creative_generate(client: TestClient):
    payload = {"scenario_ids": ["demo_scenario"], "asset_types": ["homepage_hero"]}
    resp = client.post("/api/v1/creative/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "briefs" in data
    assert data["briefs"], "expected generated briefs"
    brief = data["briefs"][0]
    assert "creative_brief" in brief
    assert "assets" in brief
