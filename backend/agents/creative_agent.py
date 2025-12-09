"""
Execution & Creative Agent

Wraps CreativeEngine to generate briefs and assets and return simple campaign plans.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any

from models.schemas import PromoScenario, CampaignPlan, CreativeBrief, AssetSpec
from engines.creative_engine import CreativeEngine
from engines.validation_engine import ValidationEngine
from tools.cdp_tool import CDPTool
from middleware.observability import trace_context


class CreativeAgent:
    """Agent for generating creative briefs and campaign assets."""
    
    def __init__(
        self,
        creative_engine: Optional[CreativeEngine] = None,
        validation_engine: Optional[ValidationEngine] = None,
        cdp_tool: Optional[CDPTool] = None,
    ):
        self.creative_engine = creative_engine or CreativeEngine(cdp_tool=cdp_tool)
        self.validation_engine = validation_engine or ValidationEngine()
        self.cdp_tool = cdp_tool or CDPTool()
    
    def finalize_campaign(
        self,
        scenarios: List[PromoScenario]
    ) -> CampaignPlan:
        """Build a simple timeline that sequences scenarios."""
        timeline: Dict[Any, List[str]] = {}
        for s in scenarios:
            timeline.setdefault(s.date_range.start_date, []).append(f"Launch {s.name}")
            timeline.setdefault(s.date_range.end_date, []).append(f"Wrap {s.name}")
        return CampaignPlan(
            scenarios=scenarios,
            timeline=timeline,
            execution_details={"channels": list({ch for s in scenarios for ch in s.channels})},
        )
    
    def generate_creative_brief(
        self,
        scenario: PromoScenario
    ) -> CreativeBrief:
        """Generate structured creative brief from scenario."""
        with trace_context("creative.brief", {"scenario": scenario.id or scenario.name}):
            return self.creative_engine.generate_creative_brief(scenario)
    
    def generate_assets(
        self,
        brief: CreativeBrief
    ) -> List[AssetSpec]:
        """Generate asset specifications and copy from creative brief."""
        with trace_context("creative.assets", {"scenario": brief.scenario_id}):
            return self.creative_engine.generate_asset_specs(brief)
