"""
Scenario Evaluation Engine

Calculates KPIs for a given scenario.

Input: PromoScenario, baseline, uplift model, context
Output: ScenarioKPI with:
- Total sales, margin, EBIT
- Breakdown by channel, department, segment
- Comparison vs baseline
"""

from typing import Optional, Dict
from datetime import timedelta

from models.schemas import (
    PromoScenario,
    ScenarioKPI,
    BaselineForecast,
    UpliftModel,
    PromoContext
)
from engines.forecast_baseline_engine import ForecastBaselineEngine
from engines.uplift_elasticity_engine import UpliftElasticityEngine
from middleware.observability import trace_function, log_metric, log_event


class ScenarioEvaluationEngine:
    """Engine for evaluating promotional scenarios and calculating KPIs."""
    
    def __init__(
        self,
        forecast_engine: Optional[ForecastBaselineEngine] = None,
        uplift_engine: Optional[UpliftElasticityEngine] = None,
    ):
        """
        Initialize Scenario Evaluation Engine.
        
        Args:
            forecast_engine: Forecast & Baseline Engine instance
            uplift_engine: Uplift & Elasticity Engine instance
        """
        self.forecast_engine = forecast_engine
        self.uplift_engine = uplift_engine
    
    @trace_function(name="scenario_evaluation", attributes={"engine": "scenario_evaluation"})
    def evaluate_scenario(
        self,
        scenario: PromoScenario,
        baseline: BaselineForecast,
        uplift_model: UpliftModel,
        context: Optional[PromoContext] = None
    ) -> ScenarioKPI:
        """
        Evaluate scenario and calculate KPIs.
        
        Args:
            scenario: PromoScenario to evaluate
            baseline: BaselineForecast for comparison
            uplift_model: UpliftModel for uplift calculations
            context: Optional PromoContext
        
        Returns:
            ScenarioKPI with sales, margin, EBIT, units and breakdowns
        """
        from engines.uplift_elasticity_engine import UpliftElasticityEngine
        
        # Initialize uplift engine if not provided
        uplift_engine = self.uplift_engine or UpliftElasticityEngine()
        uplift_engine._cached_model = uplift_model
        
        # Calculate uplift for each department/channel combination
        total_sales = 0.0
        total_margin = 0.0
        total_units = 0.0
        
        breakdown_by_channel: Dict[str, Dict[str, float]] = {}
        breakdown_by_department: Dict[str, Dict[str, float]] = {}
        
        # Process each day in the scenario date range
        from datetime import date as date_type
        current_date = scenario.date_range.start_date
        end_date = scenario.date_range.end_date
        
        while current_date <= end_date:
            # Get baseline projection for this day
            day_baseline = baseline.daily_projections.get(current_date, {
                "sales": 0.0,
                "margin": 0.0,
                "units": 0.0
            })
            
            # Calculate uplift for each department/channel
            for dept in scenario.departments:
                for channel in scenario.channels:
                    # Estimate uplift
                    uplift_pct = uplift_engine.estimate_uplift(
                        category=dept,
                        channel=channel,
                        discount=scenario.discount_percentage / 100.0,
                        context=context
                    )
                    
                    # Apply uplift to baseline (proportional by department/channel)
                    # Simplified: assume equal distribution across departments/channels
                    dept_factor = 1.0 / len(scenario.departments) if scenario.departments else 1.0
                    channel_factor = 1.0 / len(scenario.channels) if scenario.channels else 1.0
                    
                    day_sales = day_baseline["sales"] * dept_factor * channel_factor * (1 + uplift_pct)
                    day_margin_pct = day_baseline["margin"] / day_baseline["sales"] if day_baseline["sales"] > 0 else 0.2
                    # Adjust margin for discount
                    day_margin_pct = max(0.0, day_margin_pct - (scenario.discount_percentage / 100.0))
                    day_margin = day_sales * day_margin_pct
                    day_units = day_baseline["units"] * dept_factor * channel_factor * (1 + uplift_pct * 0.8)
                    
                    total_sales += day_sales
                    total_margin += day_margin
                    total_units += day_units
                    
                    # Update breakdowns
                    if channel not in breakdown_by_channel:
                        breakdown_by_channel[channel] = {"sales": 0.0, "margin": 0.0, "units": 0.0, "ebit": 0.0}
                    breakdown_by_channel[channel]["sales"] += day_sales
                    breakdown_by_channel[channel]["margin"] += day_margin
                    breakdown_by_channel[channel]["units"] += day_units
                    
                    if dept not in breakdown_by_department:
                        breakdown_by_department[dept] = {"sales": 0.0, "margin": 0.0, "units": 0.0, "ebit": 0.0}
                    breakdown_by_department[dept]["sales"] += day_sales
                    breakdown_by_department[dept]["margin"] += day_margin
                    breakdown_by_department[dept]["units"] += day_units
            
            # Move to next day
            current_date = current_date + timedelta(days=1)
        
        # Calculate EBIT (simplified: margin - fixed costs)
        # Assume fixed costs are ~10% of sales
        fixed_costs = total_sales * 0.1
        total_ebit = total_margin - fixed_costs
        
        # Update EBIT in breakdowns
        for channel in breakdown_by_channel:
            breakdown_by_channel[channel]["ebit"] = breakdown_by_channel[channel]["margin"] - (breakdown_by_channel[channel]["sales"] * 0.1)
        
        for dept in breakdown_by_department:
            breakdown_by_department[dept]["ebit"] = breakdown_by_department[dept]["margin"] - (breakdown_by_department[dept]["sales"] * 0.1)
        
        # Comparison vs baseline
        comparison_vs_baseline = {
            "sales_delta": total_sales - baseline.total_sales,
            "margin_delta": total_margin - baseline.total_margin,
            "units_delta": total_units - baseline.total_units,
            "sales_pct_change": ((total_sales - baseline.total_sales) / baseline.total_sales * 100) if baseline.total_sales > 0 else 0.0,
            "margin_pct_change": ((total_margin - baseline.total_margin) / baseline.total_margin * 100) if baseline.total_margin > 0 else 0.0,
        }
        
        kpi = ScenarioKPI(
            scenario_id=scenario.id or "unknown",
            total_sales=total_sales,
            total_margin=total_margin,
            total_ebit=total_ebit,
            total_units=total_units,
            breakdown_by_channel=breakdown_by_channel,
            breakdown_by_department=breakdown_by_department,
            breakdown_by_segment=None,  # TODO: Add segment breakdown when CDP is integrated
            comparison_vs_baseline=comparison_vs_baseline
        )
        
        # Log metrics
        log_metric("scenario.evaluation.sales", total_sales, {"scenario_id": scenario.id or "unknown"})
        log_metric("scenario.evaluation.margin", total_margin, {"scenario_id": scenario.id or "unknown"})
        log_event("scenario.evaluated", {"scenario_id": scenario.id or "unknown", "sales": total_sales})
        
        return kpi

