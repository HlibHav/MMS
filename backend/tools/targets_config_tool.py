"""
Targets / Config Tool

Business targets and configuration.

API:
get_targets(month: str) -> Targets
get_promo_constraints() -> Constraints
get_brand_rules() -> BrandRules
"""

from typing import Optional, Dict, Any

from models.schemas import Targets, Constraints, BrandRules


class TargetsConfigTool:
    """Tool for accessing business targets and configuration."""

    DEFAULT_TARGETS = {
        "2024-10": {"sales_target": 1100000.0, "margin_target": 0.24, "ebit_target": 180000.0, "units_target": 2200},
        "2024-09": {"sales_target": 950000.0, "margin_target": 0.23, "ebit_target": 150000.0, "units_target": 1800},
    }

    DEFAULT_CONSTRAINTS = Constraints(
        max_discount=0.25,  # expressed as fraction
        min_margin=0.18,
        budget_limit=350000.0,
        category_restrictions=None,
    )

    DEFAULT_BRAND_RULES = BrandRules(
        tone_guidelines=["confident", "solution-first", "clear CTA"],
        style_requirements=["use concise benefit-led headlines", "surface top 2 categories per scenario"],
        mandatory_elements=["legal disclaimer", "promo window", "channels covered"],
        prohibited_content=["overpromise on stock", "unverified claims"],
    )
    
    def __init__(self, config_source: Optional[str] = None):
        """
        Initialize Targets & Config Tool.
        
        Args:
            config_source: Optional configuration source (file path, DB connection, etc.)
        """
        self.config_source = config_source
        self._config_overrides: Dict[str, Any] = {}
    
    def get_targets(
        self,
        month: str
    ) -> Targets:
        """
        Get business targets for a specific month.
        
        Args:
            month: Month identifier (e.g., "2024-10")
        
        Returns:
            Targets object with sales, margin, EBIT targets
        """
        target_values = self.DEFAULT_TARGETS.get(month)
        if not target_values:
            # Fall back to the latest known month values to keep the API usable
            latest_month = sorted(self.DEFAULT_TARGETS.keys())[-1]
            target_values = self.DEFAULT_TARGETS[latest_month]
        return Targets(month=month, **target_values)
    
    def get_promo_constraints(
        self
    ) -> Constraints:
        """
        Get promotional constraints and limits.
        
        Returns:
            Constraints object with discount limits, margin thresholds, etc.
        """
        return self.DEFAULT_CONSTRAINTS
    
    def get_brand_rules(
        self
    ) -> BrandRules:
        """
        Get brand compliance rules.
        
        Returns:
            BrandRules object with brand guidelines
        """
        return self.DEFAULT_BRAND_RULES
    
    def get_config(
        self,
        key: str
    ) -> Optional[Any]:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
        
        Returns:
            Configuration value or None
        """
        return self._config_overrides.get(key)
