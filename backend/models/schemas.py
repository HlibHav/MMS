"""
Data Schemas

Pydantic models for data validation and serialization.

This module defines all the data structures used throughout the application.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime
from pydantic import BaseModel, Field, Extra


# Core Domain Models

class DateRange(BaseModel):
    """Date range tuple."""
    start_date: date
    end_date: date


class PromoMechanic(BaseModel):
    department: str
    channel: str
    discount_pct: float
    segments: List[str] = ["ALL"]
    notes: Optional[str] = None
    product_focus: Optional[List[str]] = None


class PromoScenario(BaseModel):
    """Promotional scenario configuration (docs-aligned, backward compatible)."""
    id: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    date_range: DateRange
    departments: Optional[List[str]] = None
    channels: Optional[List[str]] = None  # online, offline
    discount_percentage: Optional[float] = None
    mechanics: Optional[List[PromoMechanic]] = None
    segments: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        extra = Extra.allow


class PromoContext(BaseModel):
    """Context information for promotional planning."""
    geo: str
    date_range: DateRange
    events: List['Event']
    weather: Optional[Dict[str, Any]] = None
    seasonality: Optional['SeasonalityProfile'] = None
    weekend_patterns: Optional[Dict[str, float]] = None


class PromoOpportunity(BaseModel):
    """Identified promotional opportunity."""
    id: str
    title: Optional[str] = None
    promo_date_range: Optional[Dict[str, str]] = None
    date_range: Optional[DateRange] = None
    department: Optional[str] = None
    focus_departments: Optional[List[str]] = None
    channel: Optional[str] = None
    estimated_potential: Optional[Dict[str, float]] = None
    priority: Optional[str] = None
    rationale: Optional[str] = None


class BaselineForecast(BaseModel):
    """Baseline forecast without promotions."""
    date_range: DateRange
    daily_projections: Dict[date, Dict[str, float]]  # date -> {sales, margin, units}
    total_sales: float
    total_margin: float
    total_units: float
    gap_vs_target: Optional[Dict[str, float]] = None


class UpliftModel(BaseModel):
    """Uplift model with coefficients."""
    coefficients: Dict[str, Dict[str, float]]  # category -> channel -> coefficient
    version: str
    last_updated: datetime


class KPIBreakdown(BaseModel):
    channel: Optional[str] = None
    department: Optional[str] = None
    sales_value: Optional[float] = None
    margin_pct: Optional[float] = None
    units: Optional[float] = None
    margin_value: Optional[float] = None


class ScenarioKPI(BaseModel):
    """KPI results for a scenario (docs)."""
    scenario_id: Optional[str] = None
    period: Optional[str] = None
    total: Optional[Dict[str, float]] = None
    vs_baseline: Optional[Dict[str, float]] = None
    by_channel: Optional[List[KPIBreakdown]] = None
    by_department: Optional[List[KPIBreakdown]] = None
    by_segment: Optional[List[KPIBreakdown]] = None
    # backward compat fields
    total_sales: Optional[float] = None
    total_margin: Optional[float] = None
    total_ebit: Optional[float] = None
    total_units: Optional[float] = None
    breakdown_by_channel: Optional[Dict[str, Dict[str, float]]] = None
    breakdown_by_department: Optional[Dict[str, Dict[str, float]]] = None
    breakdown_by_segment: Optional[Dict[str, Dict[str, float]]] = None
    comparison_vs_baseline: Optional[Dict[str, float]] = None


class ValidationIssue(BaseModel):
    type: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    suggested_fix: Optional[str] = None
    affected_department: Optional[str] = None


class ValidationReport(BaseModel):
    """Scenario validation report."""
    scenario_id: Optional[str] = None
    status: Optional[str] = None  # PASS | WARN | BLOCK
    issues: Optional[List[ValidationIssue]] = None
    overall_score: Optional[float] = None
    # backward compat
    is_valid: Optional[bool] = None
    fixes: Optional[List[str]] = None
    checks_passed: Optional[Dict[str, bool]] = None


class CreativeBrief(BaseModel):
    """Creative brief for campaign assets."""
    scenario_id: str
    objectives: List[str]
    messaging: str
    target_audience: str
    tone: str
    style: str
    mandatory_elements: List[str]


class AssetSpec(BaseModel):
    """Asset specification."""
    asset_type: str  # homepage_hero, banner, instore, email_header
    copy_text: str
    layout_hints: Optional[Dict[str, Any]] = None
    dimensions: Optional[Dict[str, int]] = None


class CampaignPlan(BaseModel):
    """Finalized campaign plan."""
    scenarios: List[PromoScenario]
    timeline: Dict[date, List[str]]
    execution_details: Dict[str, Any]


class PostMortemReport(BaseModel):
    """Post-mortem analysis report (docs)."""
    scenario_id: str
    period: Optional[str] = None
    forecast_kpi: Optional[Any] = None
    actual_kpi: Optional[Any] = None
    vs_forecast: Optional[Dict[str, float]] = None
    post_promo_dip: Optional[Dict[str, Any]] = None
    cannibalization_signals: Optional[List[Dict[str, Any]]] = None
    insights: Optional[List[str]] = None
    learning_points: Optional[List[str]] = None
    # backward compat
    forecast_accuracy: Optional[Dict[str, float]] = None
    uplift_analysis: Optional[Dict[str, Any]] = None


class Insights(BaseModel):
    """Actionable insights."""
    key_learnings: List[str]
    recommendations: List[str]
    next_steps: List[str]


# Supporting Models

class Event(BaseModel):
    """Event or holiday."""
    name: str
    date: date
    type: str  # holiday, local_event, seasonal
    impact: Optional[str] = None


class SeasonalityProfile(BaseModel):
    """Seasonality profile for a region."""
    geo: str
    monthly_factors: Dict[int, float]  # month -> factor
    weekly_patterns: Dict[str, float]  # day_of_week -> factor


class PromoCampaign(BaseModel):
    """Historical promotional campaign."""
    id: str
    name: str
    date_range: DateRange
    departments: List[str]
    channels: List[str]
    discount_percentage: float
    actual_results: Optional[Dict[str, float]] = None


class Segment(BaseModel):
    """Customer segment."""
    id: str
    name: str
    description: Optional[str] = None
    size: Optional[float] = None  # percentage of total


class Targets(BaseModel):
    """Business targets."""
    month: str
    sales_target: float
    margin_target: float
    ebit_target: Optional[float] = None
    units_target: Optional[float] = None


class Constraints(BaseModel):
    """Promotional constraints."""
    max_discount: float
    min_margin: float
    budget_limit: Optional[float] = None
    category_restrictions: Optional[List[str]] = None


class BrandRules(BaseModel):
    """Brand compliance rules."""
    tone_guidelines: List[str]
    style_requirements: List[str]
    mandatory_elements: List[str]
    prohibited_content: List[str]


class GapAnalysis(BaseModel):
    """Gap analysis between baseline and targets."""
    sales_gap: float
    margin_gap: float
    units_gap: Optional[float] = None
    gap_percentage: Dict[str, float]


class ComparisonReport(BaseModel):
    """Scenario comparison report."""
    scenarios: List[PromoScenario]
    kpis: List[ScenarioKPI]
    comparison_table: Dict[str, List[float]]
    recommendations: List[str]


class ComplianceReport(BaseModel):
    """Brand compliance report."""
    is_compliant: bool
    issues: List[str]
    recommendations: List[str]


class ConstraintCheck(BaseModel):
    """Constraint verification result."""
    all_passed: bool
    failed_checks: List[str]
    details: Dict[str, bool]


class FrontierData(BaseModel):
    """Efficient frontier data."""
    scenarios: List[PromoScenario]
    coordinates: List[Tuple[float, float]]  # (sales, margin)
    pareto_optimal: List[bool]


class RankedScenarios(BaseModel):
    """Ranked scenarios with rationale."""
    ranked_scenarios: List[Tuple[PromoScenario, float]]  # (scenario, score)
    rationale: Dict[str, str]


class QualityReport(BaseModel):
    """Data quality report."""
    completeness: float
    accuracy: float
    consistency: float
    timeliness: float
    issues: List[str]
    recommendations: List[str]


class StorageResult(BaseModel):
    """Database storage result."""
    success: bool
    rows_inserted: int
    table_name: str
    errors: Optional[List[str]] = None


class AnalysisDataset(BaseModel):
    """Prepared dataset for analysis."""
    data: Dict[str, Any]  # DataFrame or similar
    metadata: Dict[str, Any]
    filters_applied: Dict[str, Any]


