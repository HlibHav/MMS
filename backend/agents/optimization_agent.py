"""
Optimization & Business Impact Agent

Wraps ScenarioOptimizationEngine with simple scoring and validation.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any

from models.schemas import PromoScenario, FrontierData, RankedScenarios
from engines.scenario_optimization_engine import ScenarioOptimizationEngine
from engines.scenario_evaluation_engine import ScenarioEvaluationEngine
from engines.validation_engine import ValidationEngine
from middleware.observability import trace_context


class OptimizationAgent:
    """Agent for optimizing promotional scenarios for maximum business impact."""
    
    def __init__(
        self,
        optimization_engine: Optional[ScenarioOptimizationEngine] = None,
        evaluation_engine: Optional[ScenarioEvaluationEngine] = None,
        validation_engine: Optional[ValidationEngine] = None,
    ):
        self.optimization_engine = optimization_engine or ScenarioOptimizationEngine(
            evaluation_engine=evaluation_engine,
            validation_engine=validation_engine,
        )
        self.evaluation_engine = evaluation_engine
        self.validation_engine = validation_engine
    
    def optimize_scenarios(
        self,
        brief: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[PromoScenario]:
        """Generate and score optimized scenarios based on brief and constraints."""
        with trace_context("optimization.optimize", {"brief": brief[:32]}):
            candidates = self.optimization_engine.generate_candidate_scenarios(brief, constraints)
            weights = (constraints or {}).get("weights", {"sales": 0.6, "margin": 0.4})
            ranked = self.optimization_engine.optimize_scenarios(candidates, weights, constraints)
            return ranked
    
    def calculate_efficient_frontier(
        self,
        scenarios: List[PromoScenario]
    ) -> FrontierData:
        """Return a simple frontier using discount_percentage as proxy coordinates."""
        coords = [(s.discount_percentage, s.discount_percentage * 0.6) for s in scenarios]
        pareto = [True for _ in scenarios]
        return FrontierData(scenarios=scenarios, coordinates=coords, pareto_optimal=pareto)
    
    def rank_by_objectives(
        self,
        scenarios: List[PromoScenario],
        weights: Optional[Dict[str, float]] = None
    ) -> RankedScenarios:
        """Rank scenarios by weighted discount heuristic."""
        weights = weights or {"sales": 0.6, "margin": 0.4}
        ranked = sorted(
            scenarios,
            key=lambda s: s.discount_percentage * weights.get("sales", 0.6),
            reverse=True,
        )
        rationale = {s.id or s.name: "Ranked by discount proxy" for s in ranked}
        return RankedScenarios(ranked_scenarios=[(s, idx) for idx, s in enumerate(ranked, start=1)], rationale=rationale)
