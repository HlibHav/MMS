"""
Discovery / Context Agent

Purpose: Brainstorming, understanding situation, finding opportunities.

This implementation provides a thin LangChain-inspired orchestrator that calls
existing engines/tools, applies lightweight safety checks, and returns
structured objects used by the discovery endpoints.
"""

from __future__ import annotations

import logging
from calendar import monthrange
from datetime import date
from typing import List, Optional, Dict, Any, Tuple

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional dependency at runtime
    ChatOpenAI = None

from pydantic import ValidationError

from middleware.observability import trace_context
from models.schemas import (
    PromoOpportunity,
    PromoContext,
    GapAnalysis,
    BaselineForecast,
    DateRange,
)
from engines.context_engine import ContextEngine
from engines.forecast_baseline_engine import ForecastBaselineEngine
from tools.context_data_tool import ContextDataTool
from tools.weather_tool import WeatherTool
from tools.targets_config_tool import TargetsConfigTool
from tools.sales_data_tool import SalesDataTool


logger = logging.getLogger(__name__)

# Basic stopword guardrail for generated rationales
STOPWORDS = {"suicide", "self-harm", "kill", "hate", "violence"}


class DiscoveryAgent:
    """Agent for discovering promotional opportunities and analyzing context."""
    
    def __init__(
        self,
        context_engine: Optional[ContextEngine] = None,
        forecast_engine: Optional[ForecastBaselineEngine] = None,
        context_tool: Optional[ContextDataTool] = None,
        weather_tool: Optional[WeatherTool] = None,
        targets_tool: Optional[TargetsConfigTool] = None,
        sales_tool: Optional[SalesDataTool] = None,
    ):
        """
        Initialize Discovery Agent.
        
        Args:
            context_engine: Context Engine instance
            forecast_engine: Forecast & Baseline Engine instance
            context_tool: Context Data Tool instance
            weather_tool: Weather Tool instance
            targets_tool: Targets & Config Tool instance
            sales_tool: Sales data tool for opportunity sizing
        """
        self.context_tool = context_tool or ContextDataTool()
        self.weather_tool = weather_tool or WeatherTool()
        self.targets_tool = targets_tool or TargetsConfigTool()
        self.sales_tool = sales_tool or SalesDataTool()

        self.context_engine = context_engine or ContextEngine(
            context_tool=self.context_tool,
            weather_tool=self.weather_tool,
        )
        self.forecast_engine = forecast_engine or ForecastBaselineEngine(
            sales_data_tool=self.sales_tool, targets_tool=self.targets_tool
        )

        self._llm = self._build_llm()
    
    def analyze_situation(
        self,
        month: str,
        geo: str,
        targets: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze current situation and identify promotional opportunities.
        
        Args:
            month: Target month for analysis (e.g., "2024-10")
            geo: Geographic region (e.g., "DE", "UA")
            targets: Optional targets dictionary
        
        Returns:
            Dict with baseline, gap_analysis, opportunities
        """
        start_date, end_date = self._month_to_range(month)

        with trace_context("discovery.analyze", {"month": month, "geo": geo}):
            baseline = self.forecast_engine.calculate_baseline((start_date, end_date))
            targets_dict = targets or self.targets_tool.get_targets(month).model_dump()
            gap_analysis = self.identify_gaps(baseline, targets_dict)
            context = self.get_context((start_date, end_date), geo)
            opportunities = self._generate_opportunities(
                date_range=(start_date, end_date),
                geo=geo,
                gap=gap_analysis,
                context=context,
            )

        self._validate_outputs(baseline, gap_analysis, opportunities)

        return {
            "baseline": baseline,
            "gap_analysis": gap_analysis,
            "opportunities": opportunities,
            "context": context,
        }
    
    def get_context(
        self,
        date_range: tuple,
        geo: str
    ) -> PromoContext:
        """
        Gather comprehensive context for promotional planning.
        
        Args:
            date_range: Tuple of (start_date, end_date)
            geo: Geographic region
        
        Returns:
            PromoContext object with events, weather, seasonality
        """
        start_date, end_date = date_range
        with trace_context("discovery.context", {"geo": geo}):
            return self.context_engine.build_context(
                geo=geo,
                date_range=DateRange(start_date=start_date, end_date=end_date)
            )
    
    def identify_gaps(
        self,
        baseline: BaselineForecast,
        targets: dict
    ) -> GapAnalysis:
        """
        Identify gaps between baseline forecast and targets.
        
        Args:
            baseline: Baseline forecast dictionary
            targets: Target values dictionary
        
        Returns:
            GapAnalysis object with gap details
        """
        gaps = self.forecast_engine.calculate_gap_vs_targets(baseline, targets)
        sales_target = targets.get("sales_target") or 1
        gap_percentage = {
            "sales": (gaps.get("sales_gap", 0.0) / sales_target) if sales_target else 0.0
        }
        return GapAnalysis(
            sales_gap=gaps.get("sales_gap", 0.0),
            margin_gap=gaps.get("margin_gap", 0.0),
            units_gap=gaps.get("units_gap", 0.0),
            gap_percentage=gap_percentage,
        )

    # Internal helpers
    def _generate_opportunities(
        self,
        date_range: Tuple[date, date],
        geo: str,
        gap: GapAnalysis,
        context: Optional[PromoContext] = None,
    ) -> List[PromoOpportunity]:
        """Generate a simple ranked list of opportunities."""
        agg = self.sales_tool.get_aggregated_sales(
            date_range=date_range,
            grain=["department"],
            filters={"channel": None},
        )
        opportunities: List[PromoOpportunity] = []
        if agg.empty:
            return opportunities

        # Sort by sales contribution descending
        agg = agg.sort_values(by="sales_value", ascending=False).reset_index(drop=True)
        for idx, row in agg.iterrows():
            gap_pct = gap.gap_percentage.get("sales", 0.0)
            estimated_potential = float(row["sales_value"] * (0.1 + abs(gap_pct)))
            rationale = self._generate_rationale(
                department=str(row["department"]),
                gap_pct=gap_pct,
                geo=geo,
                context=context,
            )
            try:
                opportunities.append(
                    PromoOpportunity(
                        id=f"opp_{idx+1:02d}",
                        department=row["department"],
                        channel="mixed",
                        date_range=DateRange(start_date=date_range[0], end_date=date_range[1]),
                        estimated_potential=estimated_potential,
                        priority=idx + 1,
                        rationale=rationale,
                    )
                )
            except ValidationError as exc:  # noqa: BLE001
                logger.warning("Skipping invalid opportunity: %s", exc)
                continue

        return opportunities

    def _generate_rationale(
        self,
        department: str,
        gap_pct: float,
        geo: str,
        context: Optional[PromoContext] = None,
    ) -> str:
        """Generate a short rationale, guarded by stopword filtering."""
        gap_text = f"{abs(gap_pct)*100:.1f}% below target" if gap_pct < 0 else "above target"
        weather_snippet = ""
        if context and context.weather:
            summary = context.weather.get("summary") if isinstance(context.weather, dict) else None
            if summary:
                weather_snippet = f" Weather: {summary}."
        heuristic = f"{department} in {geo} is {gap_text}; promo uplift could recover momentum.{weather_snippet}"

        if not self._llm:
            return self._sanitize(heuristic)

        prompt = (
            "You are a retail promotions assistant. "
            "Write one concise reason (max 25 words) to prioritize a department. "
            f"Department: {department}. Geo: {geo}. Gap status: {gap_text}. {weather_snippet} "
            "Avoid sensitive content."
        )
        try:
            response = self._llm.invoke(prompt).content  # type: ignore[union-attr]
            return self._sanitize(response or heuristic)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM rationale failed, using heuristic: %s", exc)
            return self._sanitize(heuristic)

    @staticmethod
    def _month_to_range(month: str) -> Tuple[date, date]:
        """Convert YYYY-MM to (start_date, end_date)."""
        year, month_num = map(int, month.split("-"))
        last_day = monthrange(year, month_num)[1]
        return date(year, month_num, 1), date(year, month_num, last_day)

    @staticmethod
    def _sanitize(text: str) -> str:
        lowered = text.lower()
        for term in STOPWORDS:
            if term in lowered:
                lowered = lowered.replace(term, "[redacted]")
        return lowered

    def _build_llm(self):
        if not ChatOpenAI:
            return None
        try:
            return ChatOpenAI(model="gpt-3.5-turbo", temperature=0.4, streaming=False)
        except Exception as exc:  # noqa: BLE001
            logger.info("LLM not configured; continuing without it (%s)", exc)
            return None

    @staticmethod
    def _validate_outputs(
        baseline: BaselineForecast,
        gap: GapAnalysis,
        opportunities: List[PromoOpportunity]
    ):
        if baseline.total_sales is None or baseline.total_margin is None:
            raise ValueError("Baseline forecast missing totals")
        if gap.gap_percentage is None:
            raise ValueError("Gap analysis missing percentage")
        for opp in opportunities:
            if opp.estimated_potential < 0:
                raise ValueError(f"Negative potential for opportunity {opp.id}")

