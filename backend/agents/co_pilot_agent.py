"""
Explainer / Co-Pilot (Chat) Agent

Thin orchestrator that can pull discovery insights and scenario context, apply
simple safeguards, and emit chat-friendly responses (sync or streamed).
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any, Generator, List

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional dependency at runtime
    ChatOpenAI = None

from middleware.observability import trace_context
from models.schemas import ValidationReport, PromoScenario, ScenarioKPI
from agents.discovery_agent import DiscoveryAgent
from agents.scenario_lab_agent import ScenarioLabAgent

logger = logging.getLogger(__name__)

STOPWORDS = {"suicide", "self-harm", "kill", "hate", "violence"}


class CoPilotAgent:
    """Agent for conversational interface and explanations."""
    
    def __init__(
        self,
        context: Optional[Dict[str, Any]] = None,
        discovery_agent: Optional[DiscoveryAgent] = None,
        scenario_agent: Optional[ScenarioLabAgent] = None,
    ):
        self.context = context or {}
        self.discovery_agent = discovery_agent
        self.scenario_agent = scenario_agent
        self._llm = self._build_llm()
    
    def generate_response(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return a structured chat response with suggestions and related data."""
        ctx = {**self.context, **(context or {})}
        related_ids = ctx.get("active_scenarios", [])

        with trace_context("copilot.message", {"screen": ctx.get("screen", "unknown")}):
            insights = self._maybe_fetch_discovery(ctx)
            scenario_insight = self._maybe_fetch_scenario(ctx)
            prompt = self._build_prompt(message, ctx, insights, scenario_insight)
            response_text = self._run_llm(prompt, fallback=self._fallback(message, ctx, insights))
            response_text = self._sanitize(response_text)

        suggestions = self._suggestions(ctx)
        return {
            "response": response_text,
            "suggestions": suggestions,
            "related_data": {"scenario_ids": related_ids},
        }

    def stream_response(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Generator[str, None, None]:
        """Yield a streamed response (word-delimited) for SSE."""
        final = self.generate_response(message, context)["response"]
        for chunk in final.split(" "):
            yield chunk

    def update_context(
        self,
        screen: Optional[str] = None,
        active_scenarios: Optional[List[str]] = None,
        validation_reports: Optional[List[ValidationReport]] = None,
        current_task: Optional[str] = None,
    ):
        if screen:
            self.context["screen"] = screen
        if active_scenarios:
            self.context["active_scenarios"] = active_scenarios
        if validation_reports:
            self.context["validation_reports"] = validation_reports
        if current_task:
            self.context["current_task"] = current_task

    # Internal helpers
    def _maybe_fetch_discovery(self, ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        month = ctx.get("month")
        geo = ctx.get("geo")
        if not (month and geo and self.discovery_agent):
            return None
        try:
            result = self.discovery_agent.analyze_situation(month=month, geo=geo, targets=ctx.get("targets"))
            return {
                "gap": result["gap_analysis"],
                "top_opportunity": result["opportunities"][0] if result["opportunities"] else None,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Discovery lookup failed: %s", exc)
            return None

    def _maybe_fetch_scenario(self, ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        scenario_data = ctx.get("scenario") or ctx.get("scenario_payload")
        if not (scenario_data and self.scenario_agent):
            return None
        try:
            scenario = scenario_data if isinstance(scenario_data, PromoScenario) else PromoScenario.model_validate(scenario_data)
            kpi: ScenarioKPI = self.scenario_agent.evaluate_scenario(scenario)
            return {"scenario": scenario, "kpi": kpi}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Scenario evaluation failed: %s", exc)
            return None

    def _build_prompt(self, message: str, ctx: Dict[str, Any], insights: Optional[Dict[str, Any]], scenario_insight: Optional[Dict[str, Any]]) -> str:
        screen = ctx.get("screen", "unknown screen")
        task = ctx.get("current_task", "explore data")
        pieces = [
            f"User message: {message}",
            f"Screen: {screen}",
            f"Current task: {task}",
        ]
        if insights and insights.get("gap"):
            gap = insights["gap"]
            pieces.append(f"Gap: sales {gap.sales_gap:.0f}, margin {gap.margin_gap:.3f}")
        if insights and insights.get("top_opportunity"):
            opp = insights["top_opportunity"]
            pieces.append(f"Top opportunity: {opp.department} potential {opp.estimated_potential:.0f}")
        if scenario_insight and scenario_insight.get("kpi"):
            kpi = scenario_insight["kpi"]
            pieces.append(f"Scenario KPI sales {kpi.total_sales:.0f}, margin {kpi.total_margin:.0f}")
        return " | ".join(pieces)

    def _run_llm(self, prompt: str, fallback: str) -> str:
        if not self._llm:
            return fallback
        try:
            with trace_context("copilot.llm", {"model": "gpt-3.5-turbo"}):
                return self._llm.invoke(prompt).content or fallback  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            logger.info("LLM call failed, using fallback: %s", exc)
            return fallback

    @staticmethod
    def _fallback(message: str, ctx: Dict[str, Any], insights: Optional[Dict[str, Any]]) -> str:
        parts = [f"I hear you on '{message}'."]
        if insights and insights.get("gap"):
            parts.append("We have a gap; focusing on the listed opportunities could help.")
        if ctx.get("screen"):
            parts.append(f"From {ctx['screen']}, consider refining parameters or running a scenario.")
        return " ".join(parts)

    @staticmethod
    def _suggestions(ctx: Dict[str, Any]) -> List[str]:
        suggestions = ["Ask for a scenario comparison", "Request gap drivers for top departments"]
        if ctx.get("screen") == "Discovery":
            suggestions.append("Generate a scenario for the highest-gap department")
        return suggestions[:3]

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
            return ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5, streaming=False)
        except Exception as exc:  # noqa: BLE001
            logger.info("LLM not configured; continuing without it (%s)", exc)
            return None

