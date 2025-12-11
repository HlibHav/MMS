"""
Learning Engine

Updates uplift models from post-mortems.

Input: Post-mortem reports, current model
Output: Updated UpliftModel

Methodology:
- Compare forecasted vs actual uplift
- Adjust coefficients by category/channel
- Weight recent data more heavily
"""

from typing import List, Optional, Dict

from models.schemas import PostMortemReport, UpliftModel


class LearningEngine:
    """Engine for learning from post-mortem reports and updating models."""
    
    def __init__(self):
        """Initialize Learning Engine."""
        self.adjustment_floor = 0.8
        self.adjustment_cap = 1.2
    
    def update_uplift_model(
        self,
        current_model: UpliftModel,
        post_mortems: List[PostMortemReport]
    ) -> UpliftModel:
        """
        Update uplift model based on post-mortem reports.
        
        Args:
            current_model: Current UpliftModel
            post_mortems: List of PostMortemReport objects
        
        Returns:
            Updated UpliftModel with adjusted coefficients
        """
        if not post_mortems or not current_model:
            raise ValueError("post_mortems and current_model are required")

        adjustments = self.calculate_model_adjustments(post_mortems)
        new_coefficients: Dict[str, Dict[str, float]] = {}

        for category, channels in current_model.coefficients.items():
            new_coefficients[category] = {}
            for channel, coef in channels.items():
                factor = adjustments.get(f"{category}:{channel}") or adjustments.get("global") or 1.0
                adjusted = coef * factor
                adjusted = max(self.adjustment_floor * coef, min(self.adjustment_cap * coef, adjusted))
                new_coefficients[category][channel] = adjusted

        return UpliftModel(
            coefficients=new_coefficients,
            version=f"{current_model.version}-learned",
            last_updated=current_model.last_updated
        )
    
    def calculate_model_adjustments(
        self,
        post_mortems: List[PostMortemReport],
        category: Optional[str] = None,
        channel: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Calculate adjustment factors for model coefficients.
        
        Args:
            post_mortems: List of PostMortemReport objects
            category: Optional category filter
            channel: Optional channel filter
        
        Returns:
            Dictionary with adjustment factors
        """
        if not post_mortems:
            return {"global": 1.0}

        adjustments: Dict[str, float] = {}
        pct_errors: List[float] = []

        for report in post_mortems:
            accuracy = report.forecast_accuracy or {}
            pct_error = accuracy.get("total_sales_pct_error")
            if pct_error is not None:
                pct_errors.append(float(pct_error))

        if pct_errors:
            avg_error = sum(pct_errors) / len(pct_errors)
            # If we over-forecast (negative error), reduce elasticity; under-forecast increase it.
            factor = 1 + (-avg_error) * 0.1
            adjustments["global"] = max(self.adjustment_floor, min(self.adjustment_cap, factor))
        else:
            adjustments["global"] = 1.0

        return adjustments

