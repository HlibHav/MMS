"""
LangChain Structured Tools for engines and utilities.

All imports are optional; if LangChain or dependencies are missing,
`build_structured_tools` returns an empty list so callers can fall back to
deterministic code paths.
"""

from datetime import date
from typing import Any, Dict, List, Optional

try:
    from langchain.tools import StructuredTool
except Exception:  # pragma: no cover - optional dep
    StructuredTool = None  # type: ignore

from backend.models.schemas import PromoScenario, DateRange


def build_structured_tools(
    context_engine=None,
    forecast_engine=None,
    uplift_engine=None,
    eval_engine=None,
    opt_engine=None,
    validation_engine=None,
) -> List[Any]:
    """Build a list of StructuredTool instances for agent executors."""
    tools: List[Any] = []
    if StructuredTool is None:
        return tools

    if context_engine:
        def _build_context(geo: str, start_date: date, end_date: date):
            dr = DateRange(start_date=start_date, end_date=end_date)
            return context_engine.build_context(geo=geo, date_range=dr)  # type: ignore[attr-defined]

        tools.append(StructuredTool.from_function(  # type: ignore[union-attr]
            _build_context,
            name="build_context",
            description="Build promotional context (events, weather, seasonality)",
        ))

    if forecast_engine:
        def _baseline(start_date: date, end_date: date):
            return forecast_engine.calculate_baseline((start_date, end_date))  # type: ignore[attr-defined]

        tools.append(StructuredTool.from_function(  # type: ignore[union-attr]
            _baseline,
            name="calculate_baseline",
            description="Baseline forecast without promotions for a date range",
        ))

    if uplift_engine:
        def _uplift(category: Optional[str] = None, channel: Optional[str] = None, discount: Optional[float] = None, historical_data: Dict[str, Any] = {}):
            if category and channel is not None and discount is not None:
                return uplift_engine.estimate_uplift(  # type: ignore[attr-defined]
                    category, channel, discount, None
                )
            return uplift_engine.build_uplift_model(historical_data, None)  # type: ignore[attr-defined]

        tools.append(StructuredTool.from_function(  # type: ignore[union-attr]
            _uplift,
            name="uplift_tool",
            description="Estimate uplift or build uplift model from historical data",
        ))

    if eval_engine:
        def _evaluate(scenario: Dict[str, Any], baseline: Optional[Dict[str, Any]] = None, uplift_model: Optional[Dict[str, Any]] = None):
            scenario_obj = PromoScenario.model_validate(scenario)
            uplift_obj = uplift_model or {"coefficients": {"generic": {"online": 0.08, "offline": 0.06}}, "version": "tool", "last_updated": date.today()}
            base_obj = baseline or {"date_range": {"start_date": date.today(), "end_date": date.today()}, "daily_projections": {}, "total_sales": 0, "total_margin": 0, "total_units": 0}
            return eval_engine.evaluate_scenario(scenario_obj, base_obj, uplift_obj)  # type: ignore[attr-defined]

        tools.append(StructuredTool.from_function(  # type: ignore[union-attr]
            _evaluate,
            name="evaluate_scenario",
            description="Evaluate scenario KPI with baseline and uplift model",
        ))

    if opt_engine:
        def _optimize(brief: str, constraints: Optional[Dict[str, Any]] = None):
            return opt_engine.optimize_scenarios(  # type: ignore[attr-defined]
                opt_engine.generate_candidate_scenarios(brief, constraints),  # type: ignore[attr-defined]
                (constraints or {}).get("objectives", {"sales": 0.6, "margin": 0.4}),
                constraints,
            )

        tools.append(StructuredTool.from_function(  # type: ignore[union-attr]
            _optimize,
            name="optimize_scenarios_tool",
            description="Generate and optimize candidate promo scenarios",
        ))

    if validation_engine:
        def _validate(scenario: Dict[str, Any], rules: Optional[Dict[str, Any]] = None):
            scenario_obj = PromoScenario.model_validate(scenario)
            return validation_engine.validate_scenario(scenario_obj, rules=rules)  # type: ignore[attr-defined]

        tools.append(StructuredTool.from_function(  # type: ignore[union-attr]
            _validate,
            name="validate_scenario_tool",
            description="Validate scenario against rules and constraints",
        ))

    return [t for t in tools if t is not None]
