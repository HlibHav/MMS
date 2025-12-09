"""
Validation Engine

Validates scenarios against business rules.

Input: Scenario, KPI, rules
Output: ValidationReport with issues and fixes

Checks:
- Discount limits
- Margin thresholds
- KPI plausibility
- Brand compliance
"""

from typing import Optional, Dict, Any, List

from models.schemas import PromoScenario, ScenarioKPI, ValidationReport
from tools.targets_config_tool import TargetsConfigTool


class ValidationEngine:
    """Engine for validating scenarios against business rules."""
    
    def __init__(
        self,
        config_tool: Optional[TargetsConfigTool] = None,
    ):
        """
        Initialize Validation Engine.
        
        Args:
            config_tool: Targets & Config Tool instance
        """
        self.config_tool = config_tool
    
    def validate_scenario(
        self,
        scenario: PromoScenario,
        kpi: Optional[ScenarioKPI] = None,
        rules: Optional[Dict[str, Any]] = None
    ) -> ValidationReport:
        """
        Validate scenario against business rules.
        
        Args:
            scenario: PromoScenario to validate
            kpi: Optional ScenarioKPI for validation
            rules: Optional validation rules dictionary
        
        Returns:
            ValidationReport with issues and fixes
        """
        issues: List[str] = []
        fixes: List[str] = []
        checks_passed: Dict[str, bool] = {}
        
        # Get constraints from config tool
        constraints = self.config_tool.get_promo_constraints() if self.config_tool else None
        
        # Check discount limits
        discount_check = self.check_discount_limits(scenario)
        checks_passed["discount_limits"] = discount_check
        if not discount_check:
            max_discount = constraints.max_discount * 100 if constraints else 25.0
            issues.append(f"Discount {scenario.discount_percentage}% exceeds maximum allowed {max_discount}%")
            fixes.append(f"Reduce discount to {max_discount}% or less")
        
        # Check margin thresholds if KPI provided
        if kpi:
            margin_check = self.check_margin_thresholds(kpi)
            checks_passed["margin_thresholds"] = margin_check
            if not margin_check:
                min_margin = constraints.min_margin if constraints else 0.18
                actual_margin = kpi.total_margin / kpi.total_sales if kpi.total_sales > 0 else 0.0
                issues.append(f"Margin {actual_margin:.2%} below minimum threshold {min_margin:.2%}")
                fixes.append(f"Increase discount or adjust product mix to achieve {min_margin:.2%} margin")
        
        # Check date range validity
        if scenario.date_range.start_date > scenario.date_range.end_date:
            issues.append("Start date is after end date")
            fixes.append("Adjust date range so start date is before end date")
            checks_passed["date_range"] = False
        else:
            checks_passed["date_range"] = True
        
        # Check departments/channels are not empty
        if not scenario.departments:
            issues.append("No departments specified")
            fixes.append("Add at least one department to the scenario")
            checks_passed["departments"] = False
        else:
            checks_passed["departments"] = True
        
        if not scenario.channels:
            issues.append("No channels specified")
            fixes.append("Add at least one channel (online/store) to the scenario")
            checks_passed["channels"] = False
        else:
            checks_passed["channels"] = True
        
        # KPI plausibility check
        if kpi:
            if kpi.total_sales < 0:
                issues.append("Total sales is negative")
                fixes.append("Review scenario parameters - sales should be positive")
                checks_passed["sales_plausibility"] = False
            else:
                checks_passed["sales_plausibility"] = True
            
            if kpi.total_margin < 0:
                issues.append("Total margin is negative")
                fixes.append("Review discount levels - margin should be positive")
                checks_passed["margin_plausibility"] = False
            else:
                checks_passed["margin_plausibility"] = True

        # Brand compliance (basic: mandatory elements exist)
        brand_rules = self.config_tool.get_brand_rules() if self.config_tool else None
        if brand_rules:
            mandatory = set(brand_rules.mandatory_elements or [])
            missing = [m for m in mandatory if m not in (scenario.metadata or {}).get("mandatory_elements", [])]
            if missing:
                issues.append(f"Missing brand mandatory elements: {', '.join(missing)}")
                fixes.append("Add mandatory brand elements to scenario metadata")
                checks_passed["brand_compliance"] = False
            else:
                checks_passed["brand_compliance"] = True
        
        is_valid = len(issues) == 0
        
        return ValidationReport(
            scenario_id=scenario.id or "unknown",
            is_valid=is_valid,
            issues=issues,
            fixes=fixes,
            checks_passed=checks_passed
        )
    
    def check_discount_limits(
        self,
        scenario: PromoScenario
    ) -> bool:
        """Check if discounts are within allowed limits."""
        constraints = self.config_tool.get_promo_constraints() if self.config_tool else None
        max_discount = constraints.max_discount * 100 if constraints else 25.0
        
        return scenario.discount_percentage <= max_discount
    
    def check_margin_thresholds(
        self,
        kpi: ScenarioKPI
    ) -> bool:
        """Check if margins meet minimum thresholds."""
        if kpi.total_sales == 0:
            return False
        
        constraints = self.config_tool.get_promo_constraints() if self.config_tool else None
        min_margin = constraints.min_margin if constraints else 0.18
        
        actual_margin = kpi.total_margin / kpi.total_sales
        return actual_margin >= min_margin

