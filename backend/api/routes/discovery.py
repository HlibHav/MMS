"""
Discovery API Routes

Endpoints for discovery and context analysis.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import date
from calendar import monthrange
import pandas as pd

from models.schemas import PromoOpportunity, PromoContext, GapAnalysis, DateRange
from engines.forecast_baseline_engine import ForecastBaselineEngine
from tools.sales_data_tool import SalesDataTool
from tools.context_data_tool import ContextDataTool
from tools.targets_config_tool import TargetsConfigTool

router = APIRouter()

sales_tool = SalesDataTool()
context_tool = ContextDataTool()
targets_tool = TargetsConfigTool()
baseline_engine = ForecastBaselineEngine(sales_data_tool=sales_tool, targets_tool=targets_tool)


def _month_to_range(month: str) -> tuple:
    """Convert YYYY-MM to (start_date, end_date)."""
    try:
        year, month_num = map(int, month.split("-"))
        last_day = monthrange(year, month_num)[1]
        return date(year, month_num, 1), date(year, month_num, last_day)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid month format, expected YYYY-MM") from exc


def _build_context(geo: str, start_date: date, end_date: date) -> PromoContext:
    """Assemble a lightweight context object from static fixtures."""
    events = context_tool.get_events(geo, (start_date, end_date))
    seasonality = context_tool.get_seasonality_profile(geo)
    weekend_patterns = context_tool.get_weekend_patterns(geo)
    return PromoContext(
        geo=geo,
        date_range=DateRange(start_date=start_date, end_date=end_date),
        events=events,
        weather=None,
        seasonality=seasonality,
        weekend_patterns=weekend_patterns,
    )

def _serialize_context(context: PromoContext) -> dict:
    """JSON-friendly serialization for PromoContext with date ranges."""
    payload = context.model_dump()
    payload["date_range"] = {
        "start_date": context.date_range.start_date.isoformat(),
        "end_date": context.date_range.end_date.isoformat(),
    }
    # Ensure event dates are ISO strings
    payload["events"] = [
        {**event, "date": event["date"].isoformat()} for event in payload.get("events", [])
    ]
    return payload


@router.post("/analyze")
async def analyze_situation(payload: dict) -> dict:
    """
    Docs-aligned discovery analysis.

    Returns baseline forecast, gap analysis, and opportunities.
    """
    month = payload.get("month")
    geo = payload.get("geo")
    if not month or not geo:
        raise HTTPException(status_code=400, detail="month and geo are required")

    start_date, end_date = _month_to_range(month)
    try:
        baseline = baseline_engine.calculate_baseline((start_date, end_date))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    targets = payload.get("targets") or targets_tool.get_targets(month).model_dump()
    gap_vs_target = baseline_engine.calculate_gap_vs_targets(baseline=baseline, targets=targets)

    # Opportunities (reuse sales aggregation)
    agg = sales_tool.get_aggregated_sales(
        date_range=(start_date, end_date),
        grain=["department"],
        filters={"channel": None},
    )
    opportunities: list[dict] = []
    if not agg.empty:
        agg = agg.sort_values(by="sales_value", ascending=False).reset_index(drop=True)
        for idx, row in agg.iterrows():
            opportunities.append(
                {
                    "id": f"opp_{idx+1:02d}",
                    "title": f"Opportunity {idx+1}",
                    "promo_date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                    },
                    "focus_departments": [row["department"]],
                    "estimated_potential": {
                        "sales_value": float(row["sales_value"] * 0.12),
                        "margin_impact": -0.3,
                    },
                    "priority": "high" if idx == 0 else "medium",
                }
            )

    margin_pct = (baseline.total_margin / baseline.total_sales * 100) if baseline.total_sales else 0.0
    return {
        "baseline_forecast": {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "totals": {
                "sales_value": baseline.total_sales,
                "margin_value": baseline.total_margin,
                "margin_pct": margin_pct,
                "units": baseline.total_units,
            },
        },
        "gap_analysis": gap_vs_target,
        "opportunities": opportunities,
    }


@router.get("/opportunities")
async def get_opportunities(
    month: str,
    geo: str,
    targets: Optional[dict] = None
) -> List[PromoOpportunity]:
    """
    Analyze situation and identify promotional opportunities.
    
    Args:
        month: Target month (e.g., "2024-10")
        geo: Geographic region
        targets: Optional targets dictionary
    
    Returns:
        List of promotional opportunities
    """
    start_date, end_date = _month_to_range(month)
    try:
        baseline = baseline_engine.calculate_baseline((start_date, end_date))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    agg = sales_tool.get_aggregated_sales(
        date_range=(start_date, end_date),
        grain=["department"],
        filters={"channel": None},
    )
    opportunities: List[PromoOpportunity] = []
    for idx, row in agg.iterrows():
        estimated_potential = {
            "sales_value": float(row["sales_value"] * 0.12),
            "margin_impact": -0.3,
        }
        opportunities.append(
            PromoOpportunity(
                id=f"opp_{idx+1:02d}",
                title=f"Opportunity {idx+1}",
                focus_departments=[row["department"]],
                channel="mixed",
                promo_date_range={"start": start_date.isoformat(), "end": end_date.isoformat()},
                estimated_potential=estimated_potential,
                priority="high" if idx == 0 else "medium",
                rationale=f"12% upside based on {row['department']} run-rate and recent demand",
            )
        )

    opportunities.sort(
        key=lambda o: (o.estimated_potential or {}).get("sales_value", 0),
        reverse=True,
    )
    return opportunities


@router.get("/dashboard")
async def get_discovery_dashboard(
    month: str,
    geo: str,
) -> dict:
    """
    Aggregate discovery dashboard data for the frontend.

    Combines baseline gaps, departmental heatmap, context, and opportunities.
    """
    start_date, end_date = _month_to_range(month)

    # Baseline & targets
    try:
        baseline = baseline_engine.calculate_baseline((start_date, end_date))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    targets = targets_tool.get_targets(month).model_dump()
    gap_vs_target = baseline.gap_vs_target or baseline_engine.calculate_gap_vs_targets(
        baseline=baseline,
        targets=targets,
    )

    # Gap percentages vs targets
    gap_percentage = {}
    if sales_target := targets.get("sales_target"):
        gap_percentage["sales"] = gap_vs_target["sales_gap"] / sales_target
    if units_target := targets.get("units_target"):
        gap_percentage["units"] = gap_vs_target["units_gap"] / units_target
    if margin_target := targets.get("margin_target"):
        gap_percentage["margin"] = gap_vs_target["margin_gap"] / max(margin_target, 1e-6)

    # Timeseries (simple even target allocation across days)
    days = sorted(baseline.daily_projections.items(), key=lambda kv: kv[0])
    per_day_target = (
        targets["sales_target"] / len(days) if targets.get("sales_target") and days else 0.0
    )
    gap_timeseries = [
        {
            "date": day.isoformat(),
            "actual": float(values.get("sales", 0.0)),
            "target": float(per_day_target),
        }
        for day, values in days
    ]

    # Heatmap by department
    dept_df = sales_tool.get_aggregated_sales(
        date_range=(start_date, end_date),
        grain=["department"],
        filters={"channel": None},
    )
    total_sales = float(dept_df["sales_value"].sum()) if not dept_df.empty else 0.0
    target_sales = float(targets.get("sales_target") or total_sales or 1.0)
    heatmap = []
    for _, row in dept_df.iterrows():
        share = (row["sales_value"] / total_sales) if total_sales else 0.0
        dept_target = target_sales * share
        gap_pct = ((dept_target - row["sales_value"]) / dept_target) if dept_target else 0.0
        heatmap.append(
            {
                "department": row["department"],
                "gap_pct": float(gap_pct),
                "sales_value": float(row["sales_value"]),
            }
        )

    # Context & opportunities
    context = _build_context(geo=geo, start_date=start_date, end_date=end_date)
    opportunities = await get_opportunities(month=month, geo=geo)  # reuse existing logic

    return {
        "month": month,
        "geo": geo,
        "summary": {
            "sales_gap": gap_vs_target.get("sales_gap", 0.0),
            "margin_gap": gap_vs_target.get("margin_gap", 0.0),
            "units_gap": gap_vs_target.get("units_gap", 0.0),
            "gap_percentage": gap_percentage,
        },
        "gap_timeseries": gap_timeseries,
        "heatmap": heatmap,
        "context": _serialize_context(context),
        "opportunities": [opp.model_dump(mode="json") for opp in opportunities],
    }


@router.get("/context")
async def get_context(
    geo: str,
    start_date: date,
    end_date: date
) -> PromoContext:
    """
    Get comprehensive context for promotional planning.
    
    Args:
        geo: Geographic region
        start_date: Start date
        end_date: End date
    
    Returns:
        PromoContext object
    """
    try:
        return _build_context(geo=geo, start_date=start_date, end_date=end_date)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/gaps")
async def get_gaps(
    month: str,
    geo: str,
    targets: Optional[dict] = None
) -> GapAnalysis:
    """
    Identify gaps between baseline and targets.
    
    Args:
        month: Target month
        geo: Geographic region
        targets: Optional targets dictionary to override defaults
    
    Returns:
        GapAnalysis object
    """
    start_date, end_date = _month_to_range(month)
    try:
        baseline = baseline_engine.calculate_baseline((start_date, end_date))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    targets = targets or targets_tool.get_targets(month).model_dump()
    gaps = baseline_engine.calculate_gap_vs_targets(baseline, targets)
    target_sales = targets.get("sales_target", 1) or 1
    gap_percentage = {"sales": gaps["sales_gap"] / target_sales}

    return GapAnalysis(
        sales_gap=gaps["sales_gap"],
        margin_gap=gaps["margin_gap"],
        units_gap=gaps["units_gap"],
        gap_percentage=gap_percentage,
    )


@router.get("/months")
async def get_available_months() -> List[str]:
    """
    Return available months (YYYY-MM) based on the sales dataset.

    This inspects the loaded sales data to avoid hard-coding month options on the frontend.
    """
    try:
        df = sales_tool._load_dataframe()  # noqa: SLF001 - internal helper is acceptable for read-only access
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to load sales data: {exc}") from exc

    if "date" not in df.columns:
        raise HTTPException(status_code=500, detail="Sales data is missing 'date' column")

    dates = pd.to_datetime(df["date"], errors="coerce").dropna()
    if dates.empty:
        raise HTTPException(status_code=404, detail="No dates available in sales data")

    months = sorted({d.strftime("%Y-%m") for d in dates}, reverse=True)
    return months
