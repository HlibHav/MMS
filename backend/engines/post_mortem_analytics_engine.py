"""
Post-Mortem Analytics Engine

Analyzes actual vs forecasted performance.

Input: Scenario, forecast, actual data
Output: PostMortemReport with:
- Forecast accuracy
- Uplift analysis
- Post-promo dip
- Cannibalization signals
"""

from typing import Optional, Dict, Any, List

from models.schemas import PromoScenario, PostMortemReport
from tools.sales_data_tool import SalesDataTool
from middleware.observability import trace_function


class PostMortemAnalyticsEngine:
    """Engine for analyzing campaign performance after execution."""
    
    def __init__(
        self,
        sales_data_tool: Optional[SalesDataTool] = None,
    ):
        """
        Initialize Post-Mortem Analytics Engine.
        
        Args:
            sales_data_tool: Sales Data Tool instance
        """
        self.sales_data_tool = sales_data_tool
    
    @trace_function(name="post_mortem.analyze", attributes={"engine": "post_mortem"})
    def analyze_performance(
        self,
        scenario: PromoScenario,
        forecast: Dict[str, Any],
        actual_data: Dict[str, Any]
    ) -> PostMortemReport:
        """
        Analyze actual performance vs forecast.
        
        Args:
            scenario: PromoScenario that was executed
            forecast: Forecasted KPIs
            actual_data: Actual sales data
        
        Returns:
            PostMortemReport with accuracy analysis
        """
        accuracy = self.calculate_forecast_accuracy(forecast, actual_data)
        uplift = self._compute_uplift(forecast, actual_data)
        cannibalization = self.detect_cannibalization(scenario, actual_data)

        post_promo_dip = uplift.get("post_promo_dip")
        cannibal_signals = cannibalization.get("signals", [])
        insights: List[str] = cannibalization.get("insights", [])

        return PostMortemReport(
            scenario_id=scenario.id or "unknown",
            forecast_accuracy=accuracy,
            uplift_analysis=uplift,
            post_promo_dip=post_promo_dip,
            cannibalization_signals=cannibal_signals,
            insights=insights,
        )
    
    def calculate_forecast_accuracy(
        self,
        forecast: Dict[str, float],
        actual: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate simple absolute and percentage errors for KPIs."""
        metrics = ["total_sales", "total_margin", "total_units"]
        accuracy: Dict[str, float] = {}
        for key in metrics:
            f_val = float(forecast.get(key, 0.0) or 0.0)
            a_val = float(actual.get(key, 0.0) or 0.0)
            error = a_val - f_val
            pct = (error / f_val) if f_val else 0.0
            accuracy[f"{key}_error"] = error
            accuracy[f"{key}_pct_error"] = pct
        return accuracy
    
    def detect_cannibalization(
        self,
        scenario: PromoScenario,
        actual_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect cannibalization effects (placeholder heuristic)."""
        signals: List[str] = []
        # If margin dropped while units rose sharply, flag possible cannibalization
        margin = float(actual_data.get("total_margin", 0.0) or 0.0)
        units = float(actual_data.get("total_units", 0.0) or 0.0)
        if units > 0 and margin < 0:
            signals.append("Margin decline with unit growth suggests cannibalization")
        return {"signals": signals, "insights": signals[:]} 

    def _compute_uplift(
        self,
        forecast: Dict[str, Any],
        actual_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Compare actual vs forecast to infer uplift and post-promo dip."""
        forecast_sales = float(forecast.get("total_sales", 0.0) or 0.0)
        actual_sales = float(actual_data.get("total_sales", 0.0) or 0.0)
        uplift = actual_sales - forecast_sales
        uplift_pct = (uplift / forecast_sales) if forecast_sales else 0.0
        post_promo_dip = float(actual_data.get("post_promo_dip", 0.0) or 0.0)
        return {
            "uplift_value": uplift,
            "uplift_pct": uplift_pct,
            "post_promo_dip": post_promo_dip,
        }
