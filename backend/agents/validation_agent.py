"""
Governance & Validation Agent

Lightweight wrapper around ValidationEngine and brand/constraint checks.
"""

from __future__ import annotations

from typing import Optional, Dict, Any

from models.schemas import PromoScenario, ValidationReport, ComplianceReport, ConstraintCheck
from engines.validation_engine import ValidationEngine
from tools.targets_config_tool import TargetsConfigTool
from middleware.observability import trace_context


class ValidationAgent:
    """Agent for validating scenarios and ensuring compliance."""
    
    def __init__(
        self,
        validation_engine: Optional[ValidationEngine] = None,
        config_tool: Optional[TargetsConfigTool] = None,
    ):
        self.config_tool = config_tool or TargetsConfigTool()
        self.validation_engine = validation_engine or ValidationEngine(config_tool=self.config_tool)
    
    def validate_scenario(
        self,
        scenario: PromoScenario,
        rules: Optional[Dict[str, Any]] = None
    ) -> ValidationReport:
        """Validate scenario against business rules."""
        with trace_context("validation.scenario", {"scenario": scenario.id or scenario.name}):
            return self.validation_engine.validate_scenario(scenario, rules)
    
    def check_brand_compliance(
        self,
        creative: dict
    ) -> ComplianceReport:
        """Check creative assets for brand compliance (basic placeholder)."""
        issues = []
        mandatory = self.config_tool.get_brand_rules().mandatory_elements
        for elem in mandatory:
            if elem not in str(creative):
                issues.append(f"Missing mandatory element: {elem}")
        return ComplianceReport(
            is_compliant=len(issues) == 0,
            issues=issues,
            recommendations=["Add mandatory brand elements"] if issues else [],
        )
    
    def verify_constraints(
        self,
        scenario: PromoScenario,
        constraints: Optional[Dict[str, Any]] = None
    ) -> ConstraintCheck:
        """Verify scenario against financial and business constraints."""
        constraints = constraints or {}
        max_discount = constraints.get("max_discount", 50.0)
        passed = scenario.discount_percentage <= max_discount
        details = {"discount_within_limit": passed}
        failed = [] if passed else ["max_discount"]
        return ConstraintCheck(all_passed=passed, failed_checks=failed, details=details)
