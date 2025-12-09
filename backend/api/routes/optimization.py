"""
Optimization API Routes

Endpoints for scenario optimization.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Body
from typing import List, Optional, Dict, Any, Tuple

from models.schemas import PromoScenario, FrontierData, RankedScenarios, ScenarioKPI, DateRange
from middleware.rate_limit import get_rate_limit
from middleware.auth import get_current_user
from middleware.errors import NotFoundError, ProcessingError
from engines.scenario_optimization_engine import ScenarioOptimizationEngine
from engines.scenario_evaluation_engine import ScenarioEvaluationEngine
from engines.forecast_baseline_engine import ForecastBaselineEngine
from engines.uplift_elasticity_engine import UpliftElasticityEngine
from engines.context_engine import ContextEngine
from engines.validation_engine import ValidationEngine
from tools.sales_data_tool import SalesDataTool
from tools.targets_config_tool import TargetsConfigTool
from tools.context_data_tool import ContextDataTool
from agents.optimization_agent import OptimizationAgent
from agents.scenario_lab_agent import ScenarioLabAgent

router = APIRouter()

# Initialize engines and tools
sales_tool = SalesDataTool()
targets_tool = TargetsConfigTool()
context_tool = ContextDataTool()
baseline_engine = ForecastBaselineEngine(sales_data_tool=sales_tool, targets_tool=targets_tool)
uplift_engine = UpliftElasticityEngine(sales_data_tool=sales_tool)
evaluation_engine = ScenarioEvaluationEngine(uplift_engine=uplift_engine)
validation_engine = ValidationEngine(config_tool=targets_tool)
optimization_engine = ScenarioOptimizationEngine(
    evaluation_engine=evaluation_engine,
    validation_engine=validation_engine
)
context_engine = ContextEngine(context_tool=context_tool)
scenario_agent = ScenarioLabAgent(
    evaluation_engine=evaluation_engine,
    validation_engine=validation_engine,
    forecast_engine=baseline_engine,
    uplift_engine=uplift_engine,
    context_engine=context_engine,
)
optimization_agent = OptimizationAgent(
    optimization_engine=optimization_engine,
    evaluation_engine=evaluation_engine,
    validation_engine=validation_engine,
)


@router.post("/optimize")
@router.post("/generate")
@get_rate_limit("optimization")
async def optimize_scenarios(
    payload: Dict[str, Any] = Body(...),
    request: Request = None,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate optimized scenarios (docs-compliant response shape).
    """
    try:
        brief = payload.get("brief", "")
        objectives = payload.get("objectives") or payload.get("constraints", {}).get("objectives") or {"sales": 0.6, "margin": 0.4}
        constraints = payload.get("constraints") or {}
        num_scenarios = int(payload.get("num_scenarios", 3))

        optimized = optimization_agent.optimize_scenarios(brief, constraints)[: max(num_scenarios, 1)]

        results = []
        for rank, scenario in enumerate(optimized, start=1):
            kpi = scenario_agent.evaluate_scenario(scenario, geo="DE")
            results.append(
                {
                    "scenario": scenario,
                    "kpi": kpi,
                    "rank": rank,
                    "score": float(rank) / len(optimized),
                }
            )

        frontier_points = [
            {
                "sales": item["kpi"].total_sales,
                "margin": (item["kpi"].total_margin / item["kpi"].total_sales * 100) if item["kpi"].total_sales else 0,
                "ebit": item["kpi"].total_ebit,
                "scenario_id": item["scenario"].id,
            }
            for item in results
        ]

        return {
            "scenarios": results,
            "efficient_frontier": {"points": frontier_points, "pareto_optimal": [p["scenario_id"] for p in frontier_points]},
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error optimizing scenarios: {str(exc)}") from exc


@router.post("/frontier")
async def calculate_frontier(
    scenarios: List[PromoScenario]
) -> FrontierData:
    """
    Calculate efficient frontier.
    
    Args:
        scenarios: List of PromoScenario objects
    
    Returns:
        FrontierData object
    """
    if not scenarios:
        raise HTTPException(status_code=400, detail="At least one scenario is required")
    
    try:
        # Evaluate all scenarios
        kpis: List[ScenarioKPI] = []
        for scenario in scenarios:
            kpi = scenario_agent.evaluate_scenario(scenario, geo="DE")
            kpis.append(kpi)
        
        # Build coordinates (sales, margin) for frontier
        coordinates: List[Tuple[float, float]] = [
            (kpi.total_sales, kpi.total_margin) for kpi in kpis
        ]
        
        # Identify Pareto-optimal scenarios (scenarios that are not dominated)
        pareto_optimal: List[bool] = []
        for i, kpi in enumerate(kpis):
            is_optimal = True
            for j, other_kpi in enumerate(kpis):
                if i != j:
                    # Check if other scenario dominates this one
                    if (other_kpi.total_sales >= kpi.total_sales and 
                        other_kpi.total_margin >= kpi.total_margin and
                        (other_kpi.total_sales > kpi.total_sales or other_kpi.total_margin > kpi.total_margin)):
                        is_optimal = False
                        break
            pareto_optimal.append(is_optimal)
        
        return FrontierData(
            scenarios=scenarios,
            coordinates=coordinates,
            pareto_optimal=pareto_optimal
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error calculating frontier: {str(exc)}") from exc


@router.get("/frontier")
async def get_frontier_sample(
    brief_id: str,
    x_axis: str = "sales",
    y_axis: str = "margin"
) -> Dict[str, Any]:
    """
    Lightweight GET frontier endpoint matching docs with sample payload.
    """
    points = [
        {"sales": 3_000_000, "margin": 0.22, "ebit": 550_000, "scenario_id": "scenario_a"},
        {"sales": 2_700_000, "margin": 0.25, "ebit": 600_000, "scenario_id": "scenario_b"},
        {"sales": 3_300_000, "margin": 0.20, "ebit": 520_000, "scenario_id": "scenario_c"},
    ]
    pareto_ids = ["scenario_a", "scenario_b"]
    return {"frontier": {"points": points, "pareto_optimal": pareto_ids, "x_axis": x_axis, "y_axis": y_axis}}


@router.post("/rank")
async def rank_scenarios(
    scenarios: List[PromoScenario],
    weights: Optional[Dict[str, float]] = None
) -> RankedScenarios:
    """
    Rank scenarios by objectives.
    
    Args:
        scenarios: List of PromoScenario objects
        weights: Optional objective weights (default: {"sales": 0.6, "margin": 0.4})
    
    Returns:
        RankedScenarios object
    """
    if not scenarios:
        raise HTTPException(status_code=400, detail="At least one scenario is required")
    
    try:
        # Default weights
        weights = weights or {"sales": 0.6, "margin": 0.4}
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        # Evaluate all scenarios
        scenario_scores: List[Tuple[PromoScenario, float]] = []
        
        for scenario in scenarios:
            kpi = scenario_agent.evaluate_scenario(scenario, geo="DE")
            
            # Calculate composite score
            # Normalize sales and margin to 0-1 scale (using max values as reference)
            # For MVP, use simple scoring
            sales_score = kpi.total_sales / 1000000.0  # Normalize to millions
            margin_score = (kpi.total_margin / kpi.total_sales) if kpi.total_sales > 0 else 0.0
            
            composite_score = (
                weights.get("sales", 0.5) * sales_score +
                weights.get("margin", 0.5) * margin_score
            )
            
            scenario_scores.append((scenario, composite_score))
        
        # Sort by score (descending)
        scenario_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Generate rationale
        rationale: Dict[str, str] = {}
        for i, (scenario, score) in enumerate(scenario_scores):
            rank = i + 1
            rationale[scenario.id or f"scenario_{i}"] = (
                f"Rank {rank}: Score {score:.3f} "
                f"(Sales weight: {weights.get('sales', 0.5):.2f}, "
                f"Margin weight: {weights.get('margin', 0.5):.2f})"
            )
        
        return RankedScenarios(
            ranked_scenarios=scenario_scores,
            rationale=rationale
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error ranking scenarios: {str(exc)}") from exc
