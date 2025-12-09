"""
Scenario Lab Agent

Purpose: Modeling and comparing promotional scenarios.
Wraps existing engines with lightweight orchestration and safety.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import date

from models.schemas import PromoScenario, ScenarioKPI, ComparisonReport, ValidationReport, DateRange
from engines.scenario_evaluation_engine import ScenarioEvaluationEngine
from engines.validation_engine import ValidationEngine
from engines.forecast_baseline_engine import ForecastBaselineEngine
from engines.uplift_elasticity_engine import UpliftElasticityEngine
from engines.context_engine import ContextEngine
from tools.sales_data_tool import SalesDataTool
from tools.targets_config_tool import TargetsConfigTool
from tools.context_data_tool import ContextDataTool
from middleware.observability import trace_context


class ScenarioLabAgent:
    """Agent for creating, evaluating, and comparing promotional scenarios."""
    
    def __init__(
        self,
        evaluation_engine: Optional[ScenarioEvaluationEngine] = None,
        validation_engine: Optional[ValidationEngine] = None,
        forecast_engine: Optional[ForecastBaselineEngine] = None,
        uplift_engine: Optional[UpliftElasticityEngine] = None,
        context_engine: Optional[ContextEngine] = None,
    ):
        self.sales_tool = SalesDataTool()
        self.targets_tool = TargetsConfigTool()
        self.context_tool = ContextDataTool()

        self.forecast_engine = forecast_engine or ForecastBaselineEngine(
            sales_data_tool=self.sales_tool,
            targets_tool=self.targets_tool,
        )
        self.uplift_engine = uplift_engine or UpliftElasticityEngine(sales_data_tool=self.sales_tool)
        self.evaluation_engine = evaluation_engine or ScenarioEvaluationEngine(uplift_engine=self.uplift_engine)
        self.validation_engine = validation_engine or ValidationEngine(config_tool=self.targets_tool)
        self.context_engine = context_engine or ContextEngine(context_tool=self.context_tool)
    
    def create_scenario(
        self,
        scenario_data: Dict[str, Any]
    ) -> PromoScenario:
        """Create a PromoScenario from a dict payload."""
        # Expect ISO dates in scenario_data["date_range"]
        if "date_range" in scenario_data and isinstance(scenario_data["date_range"], dict):
            dr = scenario_data["date_range"]
            scenario_data["date_range"] = DateRange(
                start_date=self._coerce_date(dr.get("start_date") or dr.get("start")),
                end_date=self._coerce_date(dr.get("end_date") or dr.get("end")),
            )
        scenario = PromoScenario.model_validate(scenario_data)
        return scenario
    
    def evaluate_scenario(
        self,
        scenario: PromoScenario,
        geo: str = "DE"
    ) -> ScenarioKPI:
        """Evaluate scenario and calculate KPIs."""
        with trace_context("scenario.evaluate", {"scenario_id": scenario.id or "new"}):
            baseline = self.forecast_engine.calculate_baseline(
                (scenario.date_range.start_date, scenario.date_range.end_date)
            )
            uplift_model = self.uplift_engine.build_uplift_model({})
            context = self.context_engine.build_context(
                geo=geo,
                date_range=DateRange(
                    start_date=scenario.date_range.start_date,
                    end_date=scenario.date_range.end_date,
                ),
            )
            kpi = self.evaluation_engine.evaluate_scenario(
                scenario=scenario,
                baseline=baseline,
                uplift_model=uplift_model,
                context=context,
            )
            return kpi
    
    def compare_scenarios(
        self,
        scenarios: List[PromoScenario],
        geo: str = "DE"
    ) -> ComparisonReport:
        """Compare multiple scenarios side-by-side."""
        kpis: List[ScenarioKPI] = []
        with trace_context("scenario.compare", {"count": len(scenarios)}):
            for scenario in scenarios:
                kpis.append(self.evaluate_scenario(scenario, geo=geo))
        
        comparison_table: Dict[str, List[float]] = {
            "sales": [k.total_sales for k in kpis],
            "margin": [k.total_margin for k in kpis],
            "ebit": [k.total_ebit for k in kpis],
            "units": [k.total_units for k in kpis],
        }
        recommendations: List[str] = []
        summary: Dict[str, Any] = {}
        if kpis:
            best_sales_idx = max(range(len(kpis)), key=lambda i: kpis[i].total_sales)
            best_margin_idx = max(range(len(kpis)), key=lambda i: kpis[i].total_margin)
            summary = {
                "best_sales": scenarios[best_sales_idx].id or f"scenario_{best_sales_idx+1}",
                "best_margin": scenarios[best_margin_idx].id or f"scenario_{best_margin_idx+1}",
            }
            if best_sales_idx == best_margin_idx:
                recommendations.append("Best balance of sales and margin")
            else:
                recommendations.append("One scenario maximizes sales; another maximizes margin")
        return ComparisonReport(
            scenarios=scenarios,
            kpis=kpis,
            comparison_table=comparison_table,
            recommendations=recommendations,
        )
    
    def validate_scenario(
        self,
        scenario: PromoScenario,
        kpi: Optional[ScenarioKPI] = None,
        geo: str = "DE"
    ) -> ValidationReport:
        """Validate scenario against business rules and constraints."""
        if kpi is None:
            kpi = self.evaluate_scenario(scenario, geo=geo)
        return self.validation_engine.validate_scenario(scenario, kpi)

    @staticmethod
    def _coerce_date(value: Any) -> date:
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
