"""
Scenario Lab API Routes

Endpoints for scenario creation, evaluation, and comparison.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional, Dict, Any
import uuid
from pydantic import BaseModel

from models.schemas import PromoScenario, ScenarioKPI, ValidationReport, BaselineForecast, DateRange
from engines.scenario_evaluation_engine import ScenarioEvaluationEngine
from engines.validation_engine import ValidationEngine
from engines.forecast_baseline_engine import ForecastBaselineEngine
from engines.uplift_elasticity_engine import UpliftElasticityEngine
from engines.context_engine import ContextEngine
from tools.sales_data_tool import SalesDataTool
from tools.targets_config_tool import TargetsConfigTool
from tools.context_data_tool import ContextDataTool
from agents.scenario_lab_agent import ScenarioLabAgent
from agents.validation_agent import ValidationAgent

router = APIRouter()

# Initialize engines and tools
sales_tool = SalesDataTool()
targets_tool = TargetsConfigTool()
context_tool = ContextDataTool()
baseline_engine = ForecastBaselineEngine(sales_data_tool=sales_tool, targets_tool=targets_tool)
uplift_engine = UpliftElasticityEngine(sales_data_tool=sales_tool)
evaluation_engine = ScenarioEvaluationEngine(uplift_engine=uplift_engine)
validation_engine = ValidationEngine(config_tool=targets_tool)
context_engine = ContextEngine(context_tool=context_tool)
scenario_agent = ScenarioLabAgent(
    evaluation_engine=evaluation_engine,
    validation_engine=validation_engine,
    forecast_engine=baseline_engine,
    uplift_engine=uplift_engine,
    context_engine=context_engine,
)
validation_agent = ValidationAgent(validation_engine=validation_engine, config_tool=targets_tool)

# In-memory scenario store (for demo; replace with DB in production)
SCENARIO_STORE: Dict[str, PromoScenario] = {}


class PromoDateRange(BaseModel):
    start: str
    end: str


class PromoBrief(BaseModel):
    month: str
    promo_date_range: PromoDateRange
    focus_departments: List[str]
    objectives: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None


class CreateScenarioRequest(BaseModel):
    brief: PromoBrief
    scenario_type: str = "balanced"
    parameters: Optional[Dict[str, Any]] = None


class UpdateScenarioRequest(BaseModel):
    mechanics: Optional[List[Dict[str, Any]]] = None
    departments: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    discount_pct: Optional[float] = None
    segments: Optional[List[str]] = None


class CompareRequest(BaseModel):
    scenarios: Optional[List[PromoScenario]] = None
    scenario_ids: Optional[List[str]] = None


def _build_default_scenario(
    brief: PromoBrief,
    parameters: Optional[Dict[str, Any]] = None,
    scenario_type: str = "balanced"
) -> PromoScenario:
    """Create a simple scenario object from a brief/parameters."""
    params = parameters or {}
    start_raw = params.get("start_date") or brief.promo_date_range.start
    end_raw = params.get("end_date") or brief.promo_date_range.end
    from datetime import date as date_type

    def _coerce(value):
        if isinstance(value, str):
            return date_type.fromisoformat(value)
        return value

    start_date = _coerce(start_raw)
    end_date = _coerce(end_raw)
    return PromoScenario(
        id=str(uuid.uuid4()),
        name=params.get("name", f"{brief.month} {params.get('label', 'Scenario')}"),
        description=params.get("description") or f"{scenario_type.title()} scenario for {brief.month}",
        date_range=DateRange(
            start_date=start_date,  # type: ignore[arg-type]
            end_date=end_date,      # type: ignore[arg-type]
        ),
        departments=params.get("departments", brief.focus_departments or ["TV", "Gaming"]),
        channels=params.get("channels", ["online", "store"]),
        discount_percentage=float(params.get("discount_pct", params.get("discount_percentage", 15.0))),
        segments=params.get("segments"),
        metadata={"objectives": brief.objectives or {}, "constraints": brief.constraints or {}},
    )


def _serialize_scenario(scenario: PromoScenario, label: Optional[str] = None) -> Dict[str, Any]:
    """Return a docs-friendly scenario payload."""
    mechanics = [
        {
            "department": dept,
            "channel": ch,
            "discount_pct": scenario.discount_percentage,
            "segments": scenario.segments or ["ALL"],
        }
        for dept in scenario.departments
        for ch in scenario.channels
    ]
    return {
        "id": scenario.id,
        "label": label or scenario.name,
        "name": scenario.name,
        "description": scenario.description,
        "mechanics": mechanics,
        "date_range": {
            "start": scenario.date_range.start_date.isoformat(),
            "end": scenario.date_range.end_date.isoformat(),
        },
        "departments": scenario.departments,
        "channels": scenario.channels,
        "discount_percentage": scenario.discount_percentage,
        "segments": scenario.segments,
        "metadata": scenario.metadata or {},
    }


@router.post("/create")
async def create_scenario(payload: CreateScenarioRequest) -> Dict[str, Any]:
    """
    Create a promotional scenario from brief (docs-compliant response shape).
    """
    scenario = _build_default_scenario(payload.brief, payload.parameters, payload.scenario_type)
    SCENARIO_STORE[scenario.id] = scenario

    # Evaluate immediately for demo determinism
    geo = payload.brief.objectives.get("geo", "DE") if payload.brief.objectives else "DE"
    kpi = scenario_agent.evaluate_scenario(scenario, geo=geo)
    validation = scenario_agent.validate_scenario(scenario, kpi)

    return {
        "scenario": _serialize_scenario(scenario, label=payload.scenario_type.title()),
        "kpi": kpi,
        "validation": validation,
    }


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str) -> Dict[str, Any]:
    """Get scenario details with KPIs and validation."""
    scenario = SCENARIO_STORE.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    kpi = scenario_agent.evaluate_scenario(scenario, geo="DE")
    validation = scenario_agent.validate_scenario(scenario, kpi, geo="DE")
    return {"scenario": _serialize_scenario(scenario), "kpi": kpi, "validation": validation}


@router.put("/{scenario_id}")
async def update_scenario(scenario_id: str, updated: UpdateScenarioRequest) -> Dict[str, Any]:
    """Update scenario parameters then re-evaluate."""
    if scenario_id not in SCENARIO_STORE:
        raise HTTPException(status_code=404, detail="Scenario not found")
    existing = SCENARIO_STORE[scenario_id]
    existing.departments = updated.departments or existing.departments
    existing.channels = updated.channels or existing.channels
    if updated.discount_pct is not None:
        existing.discount_percentage = updated.discount_pct
    if updated.segments is not None:
        existing.segments = updated.segments
    SCENARIO_STORE[scenario_id] = existing

    kpi = scenario_agent.evaluate_scenario(existing, geo="DE")
    validation = scenario_agent.validate_scenario(existing, kpi, geo="DE")
    return {"scenario": _serialize_scenario(existing), "kpi": kpi, "validation": validation}


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: str) -> dict:
    """Delete scenario."""
    if scenario_id not in SCENARIO_STORE:
        raise HTTPException(status_code=404, detail="Scenario not found")
    del SCENARIO_STORE[scenario_id]
    return {"deleted": True, "scenario_id": scenario_id}


@router.post("/evaluate")
async def evaluate_scenario(
    scenario: PromoScenario
) -> Dict[str, Any]:
    """
    Evaluate scenario and calculate KPIs.
    
    Args:
        scenario: PromoScenario to evaluate
    
    Returns:
        ScenarioKPI object
    """
    try:
        kpi = scenario_agent.evaluate_scenario(scenario, geo="DE")
        validation = scenario_agent.validate_scenario(scenario, kpi, geo="DE")
        return {"kpi": kpi, "validation": validation}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error evaluating scenario: {str(exc)}") from exc


@router.post("/{scenario_id}/evaluate")
async def evaluate_scenario_by_id(
    scenario_id: str
) -> Dict[str, Any]:
    """
    Docs-friendly: re-evaluate an existing scenario by id and return KPIs + validation.
    """
    scenario = SCENARIO_STORE.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return await evaluate_scenario(scenario)


@router.post("/compare")
async def compare_scenarios(
    payload: Any = Body(...)
) -> Dict[str, Any]:
    """
    Compare multiple scenarios side-by-side.
    
    Args:
        scenarios: List of PromoScenario objects
    
    Returns:
        ComparisonReport object
    """
    scenarios: List[PromoScenario] = []
    scenario_ids: Optional[List[str]] = None

    # Support both structured payload and raw list for backward compatibility
    if isinstance(payload, dict):
        scenario_ids = payload.get("scenario_ids")
        scenarios = payload.get("scenarios") or []
    elif isinstance(payload, list):
        scenarios = payload

    if not scenarios and scenario_ids:
        for sid in scenario_ids:
            stored = SCENARIO_STORE.get(sid)
            if stored:
                scenarios.append(stored)
    if not scenarios:
        raise HTTPException(status_code=400, detail="At least one scenario is required")

    scenarios = [
        s if isinstance(s, PromoScenario) else PromoScenario.model_validate(s)
        for s in scenarios
    ]
    
    try:
        comparison = scenario_agent.compare_scenarios(scenarios, geo="DE")
        kpis = comparison.kpis
        comparison_table = comparison.comparison_table
        recommendations = comparison.recommendations

        summary: Dict[str, Any] = {}
        if kpis:
            best_sales_idx = max(range(len(kpis)), key=lambda i: kpis[i].total_sales)
            best_margin_idx = max(range(len(kpis)), key=lambda i: kpis[i].total_margin)
            summary = {
                "best_sales": scenarios[best_sales_idx].id or f"scenario_{best_sales_idx+1}",
                "best_margin": scenarios[best_margin_idx].id or f"scenario_{best_margin_idx+1}",
            }
            if best_sales_idx == best_margin_idx:
                recommendations.append("Best balance of sales and margin")
            else:
                recommendations.append("One scenario maximizes sales; another maximizes margin")

        doc_scenarios = [
            {
                "id": s.id,
                "label": s.name,
                "kpi": kpis[idx],
            }
            for idx, s in enumerate(scenarios)
        ]

        return {
            "scenarios": scenarios,
            "kpis": kpis,
            "comparison_table": comparison_table,
            "recommendations": recommendations,
            "comparison": {
                "scenarios": doc_scenarios,
                "summary": summary,
            },
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error comparing scenarios: {str(exc)}") from exc


@router.post("/validate")
async def validate_scenario(
    payload: Dict[str, Any] = Body(...)
) -> ValidationReport:
    """
    Validate scenario against business rules.
    """
    try:
        scenario_data = payload.get("scenario", payload)
        kpi_data = payload.get("kpi")
        scenario = scenario_data if isinstance(scenario_data, PromoScenario) else PromoScenario.model_validate(scenario_data)
        kpi_obj = None
        if kpi_data:
            kpi_obj = kpi_data if isinstance(kpi_data, ScenarioKPI) else ScenarioKPI.model_validate(kpi_data)

        if kpi_obj is None:
            kpi_obj = scenario_agent.evaluate_scenario(scenario, geo="DE")
        
        report = validation_agent.validate_scenario(scenario, kpi_obj)
        return report
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error validating scenario: {str(exc)}") from exc
