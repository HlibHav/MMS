"""
<<<<<<< HEAD
Post-Mortem API Routes
"""

from fastapi import APIRouter, HTTPException
from backend.models.schemas import PostMortemRequest, PostMortemReport

router = APIRouter()


@router.post("/analyze", response_model=PostMortemReport)
async def analyze_postmortem(payload: PostMortemRequest) -> PostMortemReport:
    """
    Analyze completed campaign performance.
    """
    if not payload.scenario_id:
        raise HTTPException(status_code=400, detail="scenario_id required")

    return PostMortemReport(
        scenario_id=payload.scenario_id,
        forecast_accuracy={"sales_value_error_pct": -3.1, "margin_value_error_pct": -2.8},
        uplift_analysis={"notes": "Stub uplift analysis"},
        post_promo_dip=-0.02,
        cannibalization_signals=[],
        insights=["Gaming performed well", "Uplift over-estimated for TVs"],
    )


@router.get("/{scenario_id}", response_model=PostMortemReport)
async def get_postmortem(scenario_id: str) -> PostMortemReport:
    """
    Get post-mortem report for a scenario.
    """
    if not scenario_id:
        raise HTTPException(status_code=400, detail="scenario_id required")
    return PostMortemReport(
        scenario_id=scenario_id,
        forecast_accuracy={"sales_value_error_pct": -3.1, "margin_value_error_pct": -2.8},
        uplift_analysis={"notes": "Stub uplift analysis"},
        post_promo_dip=-0.02,
        cannibalization_signals=[],
        insights=["Gaming performed well", "Uplift over-estimated for TVs"],
    )
=======
Post-mortem API routes.
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any

from middleware.auth import require_analyst
from middleware.rate_limit import get_rate_limit
from agents.post_mortem_agent import PostMortemAgent
from engines.post_mortem_analytics_engine import PostMortemAnalyticsEngine
from engines.learning_engine import LearningEngine
from tools.sales_data_tool import SalesDataTool
from .scenarios import SCENARIO_STORE

router = APIRouter()

postmortem_agent = PostMortemAgent(
    analytics_engine=PostMortemAnalyticsEngine(sales_data_tool=SalesDataTool()),
    learning_engine=LearningEngine(),
    sales_data_tool=SalesDataTool(),
)


class PostMortemRequest(BaseModel):
    scenario_id: str
    actual_data: Dict[str, float]
    period: Dict[str, str]


@router.post("/analyze")
@get_rate_limit("standard")
async def analyze_postmortem(
    request: PostMortemRequest,
    http_request: Request,
    current_user=Depends(require_analyst),
) -> Dict[str, Any]:
    """Analyze completed campaign (stubbed to spec shape)."""
    scenario = SCENARIO_STORE.get(request.scenario_id) if "SCENARIO_STORE" in globals() else None  # type: ignore[name-defined]
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found for post-mortem")
    forecast = {
        "total_sales": request.actual_data.get("sales_value", 0.0),
        "total_margin": request.actual_data.get("margin_value", 0.0),
        "total_units": request.actual_data.get("units", 0.0),
    }
    report = postmortem_agent.analyze_performance(scenario, forecast=forecast, actual_data=request.actual_data)
    return {"report": report}


@router.get("/{scenario_id}")
async def get_postmortem_report(scenario_id: str) -> Dict[str, Any]:
    """
    Docs-friendly: return a stored or demo post-mortem report for a scenario.
    """
    scenario = SCENARIO_STORE.get(scenario_id) if "SCENARIO_STORE" in globals() else None  # type: ignore[name-defined]
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found for post-mortem")
    actual = {
        "sales_value": 3100000,
        "margin_value": 700000,
        "units": 17500,
    }
    forecast = {
        "total_sales": 3200000,
        "total_margin": 720000,
        "total_units": 18000,
    }
    report = postmortem_agent.analyze_performance(
        scenario,
        forecast=forecast,
        actual_data=actual,
    )
    return {"report": report}
>>>>>>> dbf51a57d90587fa2ae6397ac9a6c322b870fe89
