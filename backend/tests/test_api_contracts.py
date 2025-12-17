import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure tmp directory exists for test database
tmp_dir = Path("./tmp")
tmp_dir.mkdir(exist_ok=True)

os.environ.setdefault("DATABASE_URL", "sqlite:///./tmp/test_mms.db")
from backend.api.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


def test_auth_api_keys(client):
    resp = client.post("/api/v1/auth/api-keys", json={"name": "test", "expires_in_days": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert "api_key" in body
    assert "expires_at" in body


def test_discovery_analyze(client):
    resp = client.post("/api/v1/discovery/analyze", json={"month": "2024-10", "geo": "DE"})
    assert resp.status_code == 200
    body = resp.json()
    assert "baseline_forecast" in body
    assert "gap_analysis" in body
    assert "opportunities" in body


def test_scenarios_create_and_get(client):
    payload = {
        "brief": {
            "month": "2024-10",
            "promo_date_range": {"start_date": "2024-10-01", "end_date": "2024-10-07"},
            "focus_departments": ["TV"],
            "objectives": {"geo": "DE"},
            "constraints": {},
        },
        "scenario_type": "balanced",
    }
    create_resp = client.post("/api/v1/scenarios/create", json=payload)
    assert create_resp.status_code == 200
    created = create_resp.json()
    scenario_id = created["scenario"]["id"]

    get_resp = client.get(f"/api/v1/scenarios/{scenario_id}")
    assert get_resp.status_code == 200
    got = get_resp.json()
    assert got["scenario"]["id"] == scenario_id
