"""
Post-mortem API routes.
"""

from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from middleware.rate_limit import get_rate_limit
from db.session import get_session
from db import models as db_models
from models.schemas import PromoScenario

router = APIRouter()


class PostMortemRequest(BaseModel):
    scenario_id: str
    actual_data: Dict[str, float]
    period: Dict[str, str]


def _demo_report(scenario_id: str) -> Dict[str, Any]:
    return {
        "report": {
            "scenario_id": scenario_id,
            "forecast_kpi": {
                "total": {
                    "sales_value": 3200000,
                    "margin_value": 720000,
                    "margin_pct": 22.5,
                    "ebit": 450000,
                    "units": 18000,
                }
            },
            "actual_kpi": {
                "total": {
                    "sales_value": 3100000,
                    "margin_value": 700000,
                    "margin_pct": 22.6,
                    "ebit": 430000,
                    "units": 17500,
                }
            },
            "vs_forecast": {
                "sales_value_error_pct": -3.1,
                "margin_value_error_pct": -2.8,
                "ebit_error_pct": -4.4,
                "units_error_pct": -2.8,
            },
            "insights": ["Uplift in Gaming was over-estimated", "TV sales exceeded forecast"],
            "learning_points": ["Adjust Gaming uplift coefficient by -5%"],
        }
    }


@router.post("/analyze")
@get_rate_limit("standard")
async def analyze_postmortem(
    request: PostMortemRequest,
    db=Depends(get_session),
) -> Dict[str, Any]:
    """Analyze completed campaign (stubbed to spec shape)."""
    scenario = db.get(db_models.PromoScenario, request.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found for post-mortem")
    return _demo_report(request.scenario_id)


@router.get("/{scenario_id}")
async def get_postmortem_report(scenario_id: str, db=Depends(get_session)) -> Dict[str, Any]:
    """
    Docs-friendly: return a stored or demo post-mortem report for a scenario.
    """
    scenario = db.get(db_models.PromoScenario, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found for post-mortem")
    return _demo_report(scenario_id)
