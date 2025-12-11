"""
Scenario Lab API Routes

Endpoints for scenario creation, evaluation, and comparison.
"""

from fastapi import APIRouter, HTTPException, Body, Depends
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
from db.session import get_session
from db import models as db_models
from sqlalchemy.orm import Session

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

    dept_discounts: Dict[str, float] = {}
    if params.get("department_discounts"):
        dept_discounts = {
            k: float(v)
            for k, v in params.get("department_discounts", {}).items()
            if v is not None
        }
    elif brief.constraints and isinstance(brief.constraints, dict):
        dd = brief.constraints.get("department_discounts")
        if isinstance(dd, dict):
            dept_discounts = {k: float(v) for k, v in dd.items() if v is not None}

    # If per-department discounts provided, use their average as the scenario-level discount
    discount_from_map = None
    if dept_discounts:
        discount_from_map = sum(dept_discounts.values()) / len(dept_discounts)

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
        discount_percentage=float(params.get("discount_pct", params.get("discount_percentage", discount_from_map if discount_from_map is not None else 15.0))),
        segments=params.get("segments"),
        metadata={
            "objectives": brief.objectives or {},
            "constraints": brief.constraints or {},
            "department_discounts": dept_discounts,
        },
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


def _persist_scenario(db: Session, scenario: PromoScenario, scenario_type: str) -> db_models.PromoScenario:
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
    row = db_models.PromoScenario(
        id=scenario.id,
        label=scenario.name,
        source_opportunity_id=None,
        date_range_start=scenario.date_range.start_date,
        date_range_end=scenario.date_range.end_date,
        scenario_type=scenario_type,
        mechanics=mechanics,
    )
    db.add(row)
    return row


def _persist_kpi(db: Session, scenario_id: str, kpi: ScenarioKPI, scenario: PromoScenario | None = None) -> db_models.ScenarioKPI:
    row = db_models.ScenarioKPI(
        scenario_id=scenario_id,
        period_start=(
            scenario.date_range.start_date
            if scenario
            else (kpi.breakdown_by_channel.get("period_start") if isinstance(kpi.breakdown_by_channel, dict) else None)  # type: ignore[arg-type]
        ),
        period_end=(
            scenario.date_range.end_date
            if scenario
            else (kpi.breakdown_by_channel.get("period_end") if isinstance(kpi.breakdown_by_channel, dict) else None)  # type: ignore[arg-type]
        ),
        total_sales_value=kpi.total_sales,
        total_margin_value=kpi.total_margin,
        total_margin_pct=(kpi.total_margin / kpi.total_sales * 100) if kpi.total_sales else 0,
        total_ebit=kpi.total_ebit,
        total_units=kpi.total_units,
        sales_value_delta=kpi.comparison_vs_baseline.get("sales_delta", 0) if kpi.comparison_vs_baseline else 0,
        margin_value_delta=kpi.comparison_vs_baseline.get("margin_delta", 0) if kpi.comparison_vs_baseline else 0,
        ebit_delta=kpi.comparison_vs_baseline.get("ebit_delta", 0) if kpi.comparison_vs_baseline else 0,
        units_delta=kpi.comparison_vs_baseline.get("units_delta", 0) if kpi.comparison_vs_baseline else 0,
        kpi_breakdown={
            "by_channel": kpi.breakdown_by_channel,
            "by_department": kpi.breakdown_by_department,
            "by_segment": kpi.breakdown_by_segment,
        },
    )
    db.add(row)
    return row


def _persist_validation(db: Session, scenario_id: str, validation: ValidationReport) -> db_models.ValidationReport:
    issues_payload = []
    for issue in getattr(validation, "issues", []) or []:
        if hasattr(issue, "model_dump"):
            issues_payload.append(issue.model_dump())
        else:
            issues_payload.append(issue)
    row = db_models.ValidationReport(
        scenario_id=scenario_id,
        status=getattr(validation, "status", None) or ("PASS" if getattr(validation, "is_valid", False) else "WARN"),
        issues=issues_payload,
        overall_score=getattr(validation, "overall_score", None),
    )
    db.add(row)
    return row


@router.post("/create")
async def create_scenario(payload: CreateScenarioRequest, db: Session = Depends(get_session)) -> Dict[str, Any]:
    """
    Create a promotional scenario from brief (docs-compliant response shape).
    """
    scenario = _build_default_scenario(payload.brief, payload.parameters, payload.scenario_type)
    geo = payload.brief.objectives.get("geo", "DE") if payload.brief.objectives else "DE"
    kpi = scenario_agent.evaluate_scenario(scenario, geo=geo)
    validation = scenario_agent.validate_scenario(scenario, kpi)

    row = _persist_scenario(db, scenario, payload.scenario_type)
    _persist_kpi(db, scenario.id or row.id, kpi, scenario)
    _persist_validation(db, scenario.id or row.id, validation)
    db.commit()

    return {
        "scenario": _serialize_scenario(scenario, label=payload.scenario_type.title()),
        "kpi": kpi,
        "validation": validation,
    }


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str, db: Session = Depends(get_session)) -> Dict[str, Any]:
    """Get scenario details with KPIs and validation."""
    row: db_models.PromoScenario | None = db.get(db_models.PromoScenario, scenario_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    scenario = PromoScenario(
        id=row.id,
        name=row.label,
        description=row.scenario_type,
        date_range=DateRange(start_date=row.date_range_start, end_date=row.date_range_end),
        departments=[m.get("department") for m in row.mechanics],
        channels=list({m.get("channel") for m in row.mechanics}),
        discount_percentage=row.mechanics[0].get("discount_pct") if row.mechanics else 0,
    )
    kpi_row = db.query(db_models.ScenarioKPI).filter(db_models.ScenarioKPI.scenario_id == row.id).order_by(db_models.ScenarioKPI.created_at.desc()).first()
    validation_row = db.query(db_models.ValidationReport).filter(db_models.ValidationReport.scenario_id == row.id).first()
    kpi_payload = None
    validation_payload = None
    if kpi_row:
        kpi_payload = ScenarioKPI(
            scenario_id=row.id,
            total_sales=float(kpi_row.total_sales_value),
            total_margin=float(kpi_row.total_margin_value),
            total_ebit=float(kpi_row.total_ebit),
            total_units=float(kpi_row.total_units),
            breakdown_by_channel=kpi_row.kpi_breakdown.get("by_channel", {}),
            breakdown_by_department=kpi_row.kpi_breakdown.get("by_department", {}),
            breakdown_by_segment=kpi_row.kpi_breakdown.get("by_segment", {}),
            comparison_vs_baseline={
                "sales_delta": float(kpi_row.sales_value_delta),
                "margin_delta": float(kpi_row.margin_value_delta),
                "ebit_delta": float(kpi_row.ebit_delta),
                "units_delta": float(kpi_row.units_delta),
            },
        )
    if validation_row:
        validation_payload = ValidationReport(
            scenario_id=row.id,
            is_valid=validation_row.status == "PASS",
            issues=validation_row.issues or [],
            fixes=[],
            checks_passed={},
        )
    return {"scenario": _serialize_scenario(scenario), "kpi": kpi_payload, "validation": validation_payload}


@router.put("/{scenario_id}")
async def update_scenario(scenario_id: str, updated: UpdateScenarioRequest, db: Session = Depends(get_session)) -> Dict[str, Any]:
    """Update scenario parameters then re-evaluate."""
    row: db_models.PromoScenario | None = db.get(db_models.PromoScenario, scenario_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")

    mechanics = row.mechanics or []
    if updated.departments or updated.channels or updated.discount_pct is not None or updated.segments is not None:
        depts = updated.departments or [m.get("department") for m in mechanics] or []
        chans = updated.channels or [m.get("channel") for m in mechanics] or []
        discount = updated.discount_pct if updated.discount_pct is not None else (mechanics[0].get("discount_pct") if mechanics else 0)
        segs = updated.segments or (mechanics[0].get("segments") if mechanics else [])
        mechanics = [
            {"department": d, "channel": c, "discount_pct": discount, "segments": segs or ["ALL"]}
            for d in depts
            for c in chans
        ]
        row.mechanics = mechanics
    db.add(row)

    scenario = PromoScenario(
        id=row.id,
        name=row.label,
        description=row.scenario_type,
        date_range=DateRange(start_date=row.date_range_start, end_date=row.date_range_end),
        departments=[m.get("department") for m in mechanics],
        channels=list({m.get("channel") for m in mechanics}),
        discount_percentage=mechanics[0].get("discount_pct") if mechanics else 0,
        segments=mechanics[0].get("segments") if mechanics else [],
    )
    kpi = scenario_agent.evaluate_scenario(scenario, geo="DE")
    validation = scenario_agent.validate_scenario(scenario, kpi, geo="DE")

    _persist_kpi(db, row.id, kpi, scenario)
    _persist_validation(db, row.id, validation)
    db.commit()

    return {"scenario": _serialize_scenario(scenario), "kpi": kpi, "validation": validation}


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: str, db: Session = Depends(get_session)) -> dict:
    """Delete scenario."""
    row: db_models.PromoScenario | None = db.get(db_models.PromoScenario, scenario_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.query(db_models.ScenarioKPI).filter(db_models.ScenarioKPI.scenario_id == scenario_id).delete()
    db.query(db_models.ValidationReport).filter(db_models.ValidationReport.scenario_id == scenario_id).delete()
    db.delete(row)
    db.commit()
    return {"deleted": True, "scenario_id": scenario_id}


@router.post("/evaluate")
async def evaluate_scenario(
    scenario: PromoScenario,
    db: Session = Depends(get_session)
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
        _persist_kpi(db, scenario.id or str(uuid.uuid4()), kpi, scenario)
        _persist_validation(db, scenario.id or str(uuid.uuid4()), validation)
        db.commit()
        return {"kpi": kpi, "validation": validation}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error evaluating scenario: {str(exc)}") from exc


@router.post("/{scenario_id}/evaluate")
async def evaluate_scenario_by_id(
    scenario_id: str,
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Docs-friendly: re-evaluate an existing scenario by id and return KPIs + validation.
    """
    row: db_models.PromoScenario | None = db.get(db_models.PromoScenario, scenario_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    scenario = PromoScenario(
        id=row.id,
        name=row.label,
        description=row.scenario_type,
        date_range=DateRange(start_date=row.date_range_start, end_date=row.date_range_end),
        departments=[m.get("department") for m in row.mechanics],
        channels=list({m.get("channel") for m in row.mechanics}),
        discount_percentage=row.mechanics[0].get("discount_pct") if row.mechanics else 0,
    )
    return await evaluate_scenario(scenario, db)


@router.post("/compare")
async def compare_scenarios(
    payload: Any = Body(...),
    db: Session = Depends(get_session)
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
            row = db.get(db_models.PromoScenario, sid)
            if row:
                scenarios.append(
                    PromoScenario(
                        id=row.id,
                        name=row.label,
                        description=row.scenario_type,
                        date_range=DateRange(start_date=row.date_range_start, end_date=row.date_range_end),
                        departments=[m.get("department") for m in row.mechanics],
                        channels=list({m.get("channel") for m in row.mechanics}),
                        discount_percentage=row.mechanics[0].get("discount_pct") if row.mechanics else 0,
                        segments=row.mechanics[0].get("segments") if row.mechanics else [],
                    )
                )
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
            best_ebit_idx = max(range(len(kpis)), key=lambda i: kpis[i].total_ebit if kpis[i].total_ebit is not None else 0)
            summary = {
                "best_sales": scenarios[best_sales_idx].id or f"scenario_{best_sales_idx+1}",
                "best_margin": scenarios[best_margin_idx].id or f"scenario_{best_margin_idx+1}",
                "best_ebit": scenarios[best_ebit_idx].id or f"scenario_{best_ebit_idx+1}",
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
