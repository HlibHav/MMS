"""
Creative API Routes

Endpoints for creative brief and asset generation.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from datetime import date, timedelta

from models.schemas import PromoScenario, CampaignPlan, CreativeBrief, AssetSpec
from engines.creative_engine import CreativeEngine
from tools.targets_config_tool import TargetsConfigTool
from tools.cdp_tool import CDPTool
from agents.creative_agent import CreativeAgent
from engines.validation_engine import ValidationEngine
from .scenarios import SCENARIO_STORE

router = APIRouter()

# Initialize engines and tools
config_tool = TargetsConfigTool()
cdp_tool = CDPTool()
creative_engine = CreativeEngine(cdp_tool=cdp_tool, config_tool=config_tool)
creative_agent = CreativeAgent(creative_engine=creative_engine, validation_engine=ValidationEngine(), cdp_tool=cdp_tool)
BRIEF_STORE: Dict[str, Dict[str, Any]] = {}


@router.post("/finalize")
async def finalize_campaign(
    scenarios: List[PromoScenario]
) -> CampaignPlan:
    """
    Finalize selected scenarios into campaign plan.
    
    Args:
        scenarios: List of selected PromoScenario objects
    
    Returns:
        CampaignPlan object
    """
    if not scenarios:
        raise HTTPException(status_code=400, detail="At least one scenario is required")
    
    try:
        return creative_agent.finalize_campaign(scenarios)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error finalizing campaign: {str(exc)}") from exc


@router.post("/brief")
async def generate_brief(
    scenario: PromoScenario,
    segments: Optional[List[str]] = None
) -> CreativeBrief:
    """
    Generate creative brief from scenario.
    
    Args:
        scenario: PromoScenario to generate brief for
        segments: Optional list of target segments
    
    Returns:
        CreativeBrief object
    """
    try:
        return creative_agent.generate_creative_brief(
            scenario=scenario,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error generating brief: {str(exc)}") from exc


@router.post("/assets")
async def generate_assets(
    brief: CreativeBrief
) -> List[AssetSpec]:
    """
    Generate asset specifications from creative brief.
    
    Args:
        brief: CreativeBrief to generate assets from
    
    Returns:
        List of AssetSpec objects
    """
    try:
        return creative_agent.generate_assets(brief)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error generating assets: {str(exc)}") from exc


@router.post("/generate")
async def generate_creative_package(payload: dict) -> dict:
    """
    Docs-friendly endpoint: generate creative brief and assets for scenarios.
    """
    scenario_ids = payload.get("scenario_ids") or []
    asset_types = payload.get("asset_types") or ["homepage_hero", "category_banner"]
    target_segments = payload.get("target_segments") or ["LOYAL_HIGH_VALUE"]

    briefs = []
    for scenario_id in scenario_ids or ["demo_scenario"]:
        scenario = SCENARIO_STORE.get(scenario_id) if "SCENARIO_STORE" in globals() else None  # type: ignore[name-defined]
        if not scenario:
            from datetime import date, timedelta
            from models.schemas import DateRange

            today = date.today()
            scenario = PromoScenario(
                id=scenario_id,
                name="Demo Scenario",
                description="Demo creative scenario",
                date_range=DateRange(start_date=today, end_date=today + timedelta(days=7)),
                departments=["TV", "Gaming"],
                channels=["online", "store"],
                discount_percentage=15.0,
            )
        brief = creative_agent.generate_creative_brief(scenario=scenario)
        assets = creative_agent.generate_assets(brief)
        filtered_assets = [a for a in assets if a.asset_type in asset_types] or assets
        brief_id = scenario_id or f"brief_{len(BRIEF_STORE)+1}"
        payload = {"brief_id": brief_id, "scenario_id": scenario_id, "creative_brief": brief, "assets": filtered_assets}
        BRIEF_STORE[brief_id] = payload
        briefs.append(payload)

    return {"briefs": briefs}


@router.get("/{brief_id}")
async def get_creative_brief(brief_id: str) -> dict:
    """
    Return stored or demo creative brief by id (docs-aligned).
    """
    stored = BRIEF_STORE.get(brief_id)
    if stored:
        return {"brief": stored.get("creative_brief"), "assets": stored.get("assets"), "brief_id": brief_id}

    # Fallback demo payload
    demo_brief = CreativeBrief(
        scenario_id="demo_scenario",
        objectives=["Close October sales gap", "Maintain margin"],
        messaging="Member-exclusive savings on TVs and Gaming",
        target_audience="LOYAL_HIGH_VALUE",
        tone="energetic",
        style="bold",
        mandatory_elements=["Brand logo", "Legal copy"],
    )
    demo_assets = creative_agent.generate_assets(demo_brief)
    return {"brief": demo_brief, "assets": demo_assets, "brief_id": brief_id}
