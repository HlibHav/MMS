"""
Post-Mortem & Learning Agent

Wraps PostMortemAnalyticsEngine and LearningEngine to analyze and update models.
"""

from __future__ import annotations

from typing import List, Optional

from models.schemas import PromoScenario, PostMortemReport, UpliftModel, Insights
from engines.post_mortem_analytics_engine import PostMortemAnalyticsEngine
from engines.learning_engine import LearningEngine
from tools.sales_data_tool import SalesDataTool
from middleware.observability import trace_context


class PostMortemAgent:
    """Agent for analyzing campaign performance and learning from results."""
    
    def __init__(
        self,
        analytics_engine: Optional[PostMortemAnalyticsEngine] = None,
        learning_engine: Optional[LearningEngine] = None,
        sales_data_tool: Optional[SalesDataTool] = None,
    ):
        self.analytics_engine = analytics_engine or PostMortemAnalyticsEngine(sales_data_tool=sales_data_tool)
        self.learning_engine = learning_engine or LearningEngine()
        self.sales_data_tool = sales_data_tool or SalesDataTool()
    
    def analyze_performance(
        self,
        scenario: PromoScenario,
        forecast: dict,
        actual_data: dict
    ) -> PostMortemReport:
        """Analyze actual performance vs forecast."""
        with trace_context("postmortem.analyze", {"scenario": scenario.id or scenario.name}):
            return self.analytics_engine.analyze_performance(scenario, forecast, actual_data)
    
    def update_uplift_model(
        self,
        post_mortems: List[PostMortemReport]
    ) -> UpliftModel:
        """Update uplift model based on post-mortem reports."""
        return self.learning_engine.update_uplift_model(post_mortems)
    
    def generate_insights(
        self,
        report: PostMortemReport
    ) -> Insights:
        """Generate actionable insights from post-mortem report."""
        return self.learning_engine.generate_insights(report)
