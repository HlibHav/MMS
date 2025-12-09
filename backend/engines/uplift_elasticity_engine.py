"""
Uplift & Elasticity Engine

Estimates promotional uplift by category/channel.

Input: Historical promo data, context
Output: UpliftModel with coefficients

Methodology:
- Compare promo vs non-promo days
- Calculate uplift by discount band
- Adjust for context (weather, events)
- Segment-specific sensitivity
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from models.schemas import UpliftModel, PromoContext
from tools.sales_data_tool import SalesDataTool
from tools.promo_catalog_tool import PromoCatalogTool


class UpliftElasticityEngine:
    """Engine for estimating promotional uplift and elasticity."""
    
    def __init__(
        self,
        sales_data_tool: Optional[SalesDataTool] = None,
        promo_catalog_tool: Optional[PromoCatalogTool] = None,
    ):
        """
        Initialize Uplift & Elasticity Engine.
        
        Args:
            sales_data_tool: Sales Data Tool instance
            promo_catalog_tool: Promo Catalog Tool instance
        """
        self.sales_data_tool = sales_data_tool
        self.promo_catalog_tool = promo_catalog_tool
        self._cached_model: Optional[UpliftModel] = None
    
    def estimate_uplift(
        self,
        category: str,
        channel: str,
        discount: float,
        context: Optional[PromoContext] = None
    ) -> float:
        """
        Estimate uplift percentage for given parameters.
        
        Args:
            category: Product category/department
            channel: Sales channel (online/offline)
            discount: Discount percentage
            context: Optional PromoContext
        
        Returns:
            Uplift percentage
        """
        # Get or build uplift model
        if self._cached_model is None:
            self._cached_model = self.build_uplift_model({})

        # Get coefficient for category/channel
        coefficients = self._cached_model.coefficients
        category_key = category.upper()
        channel_key = channel.lower()

        # Default uplift coefficient (base elasticity)
        base_coefficient = coefficients.get(category_key, {}).get(channel_key, 1.5)

        # Calculate uplift: discount * elasticity coefficient
        # Apply diminishing returns for higher discounts
        uplift = discount * base_coefficient * (1 - discount * 0.3)

        # Discount band adjustments (steeper diminishing returns above 30%)
        if discount > 0.3:
            uplift *= 0.8
        elif discount > 0.2:
            uplift *= 0.9
        
        # Adjust for context if provided
        if context:
            # Weather adjustment (simplified)
            if context.weather:
                weather_factor = context.weather.get('impact_factor', 1.0)
                uplift *= weather_factor
            
            # Event adjustment
            if context.events:
                event_boost = min(len(context.events) * 0.05, 0.2)
                uplift *= (1 + event_boost)
        
        return max(0.0, uplift)
    
    def build_uplift_model(
        self,
        historical_data: Dict[str, Any],
        context: Optional[PromoContext] = None
    ) -> UpliftModel:
        """
        Build uplift model from historical promotional data.
        
        Args:
            historical_data: Dictionary with historical promo data
            context: Optional PromoContext
        
        Returns:
            UpliftModel with coefficients by category/channel
        """
        coefficients: Dict[str, Dict[str, float]] = {}
        
        if self.sales_data_tool:
            # Get historical data (last 90 days)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)
            
            try:
                # Get aggregated sales with promo flag
                df = self.sales_data_tool.get_aggregated_sales(
                    date_range=(start_date, end_date),
                    grain=["department", "channel", "promo_flag"],
                )
                
                # Calculate uplift coefficients by comparing promo vs non-promo
                for dept in df["department"].unique():
                    dept_key = dept.upper()
                    coefficients[dept_key] = {}
                    
                    for channel in df["channel"].unique():
                        channel_key = channel.lower()
                        
                        # Get promo and non-promo sales
                        promo_data = df[
                            (df["department"] == dept) &
                            (df["channel"] == channel) &
                            (df["promo_flag"].str.lower() == "true")
                        ]
                        non_promo_data = df[
                            (df["department"] == dept) &
                            (df["channel"] == channel) &
                            (df["promo_flag"].str.lower() == "false")
                        ]
                        
                        if not promo_data.empty and not non_promo_data.empty:
                            promo_avg = promo_data["sales_value"].mean()
                            non_promo_avg = non_promo_data["sales_value"].mean()
                            avg_discount = promo_data["discount_pct"].mean()
                            
                            if non_promo_avg > 0 and avg_discount > 0:
                                # Calculate elasticity: uplift_percentage / discount_percentage
                                uplift_pct = (promo_avg - non_promo_avg) / non_promo_avg
                                elasticity = uplift_pct / avg_discount if avg_discount > 0 else 1.5
                                coefficients[dept_key][channel_key] = max(0.5, min(3.0, elasticity))
                            else:
                                coefficients[dept_key][channel_key] = 1.5  # Default
                        else:
                            coefficients[dept_key][channel_key] = 1.5  # Default
            except Exception:
                # Fallback to defaults if data unavailable
                pass
        
        # Set defaults for missing categories/channels
        default_categories = ["TV", "GAMING", "AUDIO"]
        default_channels = ["online", "store"]
        
        for cat in default_categories:
            if cat not in coefficients:
                coefficients[cat] = {}
            for ch in default_channels:
                if ch not in coefficients[cat]:
                    coefficients[cat][ch] = 1.5  # Default elasticity
        
        return UpliftModel(
            coefficients=coefficients,
            version="1.0",
            last_updated=datetime.now()
        )
