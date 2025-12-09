"""
Data Schemas

Pydantic models for data validation and serialization.

This module defines all the data structures used throughout the application.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime
from pydantic import BaseModel, Field


# Core Domain Models

class DateRange(BaseModel):
    """Date range tuple."""
    start_date: date
    end_date: date


class PromoScenario(BaseModel):
    """Promotional scenario configuration."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    date_range: DateRange
    departments: List[str]
    channels: List[str]  # online, offline
    discount_percentage: float
    segments: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


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
    department: str
    channel: str
    date_range: DateRange
    estimated_potential: float
    priority: int
    rationale: str


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


class ScenarioKPI(BaseModel):
    """KPI results for a scenario."""
    scenario_id: str
    total_sales: float
    total_margin: float
    total_ebit: float
    total_units: float
    breakdown_by_channel: Dict[str, Dict[str, float]]
    breakdown_by_department: Dict[str, Dict[str, float]]
    breakdown_by_segment: Optional[Dict[str, Dict[str, float]]] = None
    comparison_vs_baseline: Dict[str, float]


class ValidationReport(BaseModel):
    """Scenario validation report."""
    scenario_id: str
    is_valid: bool
    issues: List[str]
    fixes: List[str]
    checks_passed: Dict[str, bool]


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
    """Post-mortem analysis report."""
    scenario_id: str
    forecast_accuracy: Dict[str, float]
    uplift_analysis: Dict[str, Any]
    post_promo_dip: Optional[float] = None
    cannibalization_signals: Optional[List[str]] = None
    insights: List[str]


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


