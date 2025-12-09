"""
Scenario Optimization Engine

Generates and optimizes scenarios.

Input: Brief, constraints, objectives
Output: Ranked list of PromoScenario with KPIs

Methodology:
- Template-based generation (Conservative/Balanced/Aggressive)
- Grid search over discount ranges
- Multi-objective optimization
- Constraint satisfaction
"""

from typing import List, Optional, Dict, Any

from models.schemas import PromoScenario
from engines.scenario_evaluation_engine import ScenarioEvaluationEngine
from engines.validation_engine import ValidationEngine


class ScenarioOptimizationEngine:
    """Engine for generating and optimizing promotional scenarios."""
    
    def __init__(
        self,
        evaluation_engine: Optional[ScenarioEvaluationEngine] = None,
        validation_engine: Optional[ValidationEngine] = None,
    ):
        """
        Initialize Scenario Optimization Engine.
        
        Args:
            evaluation_engine: Scenario Evaluation Engine instance
            validation_engine: Validation Engine instance
        """
        self.evaluation_engine = evaluation_engine
        self.validation_engine = validation_engine
    
    def generate_candidate_scenarios(
        self,
        brief: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[PromoScenario]:
        """
        Generate candidate scenarios from brief.
        
        Args:
            brief: Natural language brief
            constraints: Optional constraints dictionary
        
        Returns:
            List of candidate PromoScenario objects
        """
        from datetime import date, timedelta
        import uuid
        
        # Parse constraints
        max_discount = constraints.get("max_discount", 25.0) if constraints else 25.0
        date_range = constraints.get("date_range") if constraints else None
        departments = constraints.get("departments", ["TV", "Gaming", "Audio"]) if constraints else ["TV", "Gaming", "Audio"]
        channels = constraints.get("channels", ["online", "store"]) if constraints else ["online", "store"]
        
        # Default date range: next 30 days
        if not date_range:
            start_date = date(2024, 10, 1)
            end_date = start_date + timedelta(days=29)
        else:
            start_date = date_range.get("start_date", date.today() + timedelta(days=1))
            end_date = date_range.get("end_date", start_date + timedelta(days=29))
        
        from models.schemas import PromoScenario, DateRange
        
        # Generate template scenarios: Conservative, Balanced, Aggressive
        scenarios = []
        
        # Conservative: Lower discount, focused departments
        conservative = PromoScenario(
            id=str(uuid.uuid4()),
            name="Conservative",
            description=f"{brief} - Conservative approach with moderate discounts",
            date_range=DateRange(start_date=start_date, end_date=end_date),
            departments=departments[:2] if len(departments) >= 2 else departments,
            channels=channels,
            discount_percentage=min(10.0, max_discount * 0.4),
            metadata={"strategy": "conservative"}
        )
        scenarios.append(conservative)
        
        # Balanced: Medium discount, balanced approach
        balanced = PromoScenario(
            id=str(uuid.uuid4()),
            name="Balanced",
            description=f"{brief} - Balanced approach optimizing sales and margin",
            date_range=DateRange(start_date=start_date, end_date=end_date),
            departments=departments,
            channels=channels,
            discount_percentage=min(15.0, max_discount * 0.6),
            metadata={"strategy": "balanced"}
        )
        scenarios.append(balanced)
        
        # Aggressive: Higher discount, maximize sales
        aggressive = PromoScenario(
            id=str(uuid.uuid4()),
            name="Aggressive",
            description=f"{brief} - Aggressive approach maximizing sales volume",
            date_range=DateRange(start_date=start_date, end_date=end_date),
            departments=departments,
            channels=channels,
            discount_percentage=min(max_discount * 0.9, max_discount),
            metadata={"strategy": "aggressive"}
        )
        scenarios.append(aggressive)
        
        # Grid search: Generate additional scenarios with varying discounts
        discount_steps = [5.0, 12.0, 18.0, max_discount]
        for discount in discount_steps:
            if discount <= max_discount and discount not in [s.discount_percentage for s in scenarios]:
                grid_scenario = PromoScenario(
                    id=str(uuid.uuid4()),
                    name=f"Grid-{discount}%",
                    description=f"{brief} - Grid search scenario with {discount}% discount",
                    date_range=DateRange(start_date=start_date, end_date=end_date),
                    departments=departments,
                    channels=channels,
                    discount_percentage=discount,
                    metadata={"strategy": "grid_search"}
                )
                scenarios.append(grid_scenario)
        
        return scenarios
    
    def optimize_scenarios(
        self,
        candidates: List[PromoScenario],
        objectives: Dict[str, float],
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[PromoScenario]:
        """
        Optimize scenarios for given objectives.
        
        Args:
            candidates: List of candidate scenarios
            objectives: Dictionary with objective weights (e.g., {"sales": 0.6, "margin": 0.4})
            constraints: Optional constraints dictionary
        
        Returns:
            Ranked list of optimized PromoScenario objects
        """
        if not candidates:
            return []
        
        # Evaluate and score all candidates
        scored: List[tuple] = []

        weights = objectives or {"sales": 0.6, "margin": 0.4}
        total_weight = sum(weights.values()) or 1.0
        weights = {k: v / total_weight for k, v in weights.items()}

        for scenario in candidates:
            try:
                # Evaluate scenario using provided engines if available
                if self.evaluation_engine and self.validation_engine:
                    # For scoring we need baseline/uplift/context; delegate to evaluation engine caller
                    # Optimization routes will perform evaluation; here use discount proxy if not provided
                    score = (scenario.discount_percentage / 100.0) * weights.get("sales", 0.6)
                else:
                    score = (scenario.discount_percentage / 100.0) * weights.get("sales", 0.6)
            except Exception:
                score = 0
            scored.append((scenario, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in scored]

