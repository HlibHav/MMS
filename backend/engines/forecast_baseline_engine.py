"""
Forecast & Baseline Engine

Calculates baseline forecasts without promotions.

Input: Historical sales data, context, targets
Output: BaselineForecast with daily projections

Methodology:
- Day-of-week patterns
- Seasonal adjustments
- Trend analysis
- Gap calculation vs targets
"""

from typing import Optional, Dict, Any
from datetime import date

import pandas as pd

from models.schemas import BaselineForecast, PromoContext, DateRange
from tools.sales_data_tool import SalesDataTool
from tools.targets_config_tool import TargetsConfigTool
from middleware.observability import trace_function, log_metric


class ForecastBaselineEngine:
    """Engine for calculating baseline forecasts."""
    
    def __init__(
        self,
        sales_data_tool: Optional[SalesDataTool] = None,
        targets_tool: Optional[TargetsConfigTool] = None,
    ):
        """
        Initialize Forecast & Baseline Engine.
        
        Args:
            sales_data_tool: Sales Data Tool instance
            targets_tool: Targets & Config Tool instance
        """
        self.sales_data_tool = sales_data_tool
        self.targets_tool = targets_tool
    
    @trace_function(name="baseline_calculation", attributes={"engine": "forecast_baseline"})
    def calculate_baseline(
        self,
        date_range: tuple,
        context: Optional[PromoContext] = None,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> BaselineForecast:
        """
        Calculate baseline forecast without promotions.
        
        Args:
            date_range: Tuple of (start_date, end_date)
            context: Optional PromoContext
            historical_data: Optional historical sales data
        
        Returns:
            BaselineForecast with daily projections
        """
        start_date, end_date = date_range
        # Use provided historical data or pull from the sales tool
        if historical_data is not None:
            hist_df = pd.DataFrame(historical_data)
        else:
            hist_df = self.sales_data_tool.get_daily_sales(date_range=(start_date, end_date))

        if hist_df.empty:
            raise ValueError("No historical sales data available for the requested date range")

        hist_df["day_name"] = pd.to_datetime(hist_df["date"]).dt.day_name()
        dow_means = hist_df.groupby("day_name")[["sales_value", "margin_value", "units"]].mean()
        overall_means = hist_df[["sales_value", "margin_value", "units"]].mean()

        daily_projections: Dict[date, Dict[str, float]] = {}
        totals = {"sales_value": 0.0, "margin_value": 0.0, "units": 0.0}

        for current_date in pd.date_range(start=start_date, end=end_date, freq="D"):
            dow = current_date.day_name()
            if dow in dow_means.index:
                row = dow_means.loc[dow]
            else:
                row = overall_means

            day_projection = {
                "sales": float(row["sales_value"]),
                "margin": float(row["margin_value"]),
                "units": float(row["units"]),
            }
            daily_projections[current_date.date()] = day_projection
            totals["sales_value"] += day_projection["sales"]
            totals["margin_value"] += day_projection["margin"]
            totals["units"] += day_projection["units"]

        baseline = BaselineForecast(
            date_range=DateRange(start_date=start_date, end_date=end_date),
            daily_projections=daily_projections,
            total_sales=totals["sales_value"],
            total_margin=totals["margin_value"],
            total_units=totals["units"],
            gap_vs_target=None,
        )

        if self.targets_tool:
            month_key = start_date.strftime("%Y-%m")
            targets = self.targets_tool.get_targets(month_key)
            baseline.gap_vs_target = self.calculate_gap_vs_targets(
                baseline=baseline,
                targets=targets.model_dump(),
            )
        
        # Log metrics
        log_metric("baseline.forecast.sales", baseline.total_sales)
        log_metric("baseline.forecast.margin", baseline.total_margin)

        return baseline
    
    def calculate_gap_vs_targets(
        self,
        baseline: BaselineForecast,
        targets: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate gap between baseline forecast and targets.
        
        Args:
            baseline: BaselineForecast
            targets: Dictionary with target values
        
        Returns:
            Dictionary with gap values
        """
        sales_target = targets.get("sales_target")
        units_target = targets.get("units_target")
        margin_target_pct = targets.get("margin_target")

        current_margin_pct = (
            (baseline.total_margin / baseline.total_sales) if baseline.total_sales else 0.0
        )

        return {
            "sales_gap": baseline.total_sales - sales_target if sales_target is not None else 0.0,
            "units_gap": baseline.total_units - units_target if units_target is not None else 0.0,
            "margin_gap": current_margin_pct - margin_target_pct if margin_target_pct is not None else 0.0,
        }
