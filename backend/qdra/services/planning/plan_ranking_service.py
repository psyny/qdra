from typing import List, Dict, Set

from domain.planning.output_planner import (
    PlanCandidate,
    PlanSummary,
    RankingRequest,
    RankingResult,
    RankingCriterion,
    RankingCriterionType,
    ParameterConstraintSpec,
)
from services.planning.plan_summary_service import PlanSummaryService


class PlanRankingService:
    """Service for ranking candidate plans by user-defined criteria."""

    def __init__(self):
        self.summary_service = PlanSummaryService()

    def rank_plans(
        self,
        plans: List[PlanCandidate],
        ranking_request: RankingRequest,
    ) -> tuple[List[RankingResult], List[str]]:
        """Rank plans by each criterion and return rankings with remaining plan IDs."""
        # Compute summaries for all plans
        summaries: Dict[str, PlanSummary] = {}
        for plan in plans:
            summaries[plan.plan_id] = self.summary_service.compute_summary(plan)

        # Rank by each criterion
        rankings: List[RankingResult] = []
        ranked_plan_ids: Set[str] = set()

        for criterion in ranking_request.criteria:
            result = self._rank_by_criterion(
                plans, summaries, criterion, ranking_request.max_plans_per_criterion
            )
            rankings.append(result)
            ranked_plan_ids.update(result.ranked_plan_ids)

        # Find remaining plan IDs
        all_plan_ids = {plan.plan_id for plan in plans}
        remaining_plan_ids = list(all_plan_ids - ranked_plan_ids)

        return rankings, remaining_plan_ids

    def _rank_by_criterion(
        self,
        plans: List[PlanCandidate],
        summaries: Dict[str, PlanSummary],
        criterion: RankingCriterion,
        max_plans: int,
    ) -> RankingResult:
        """Rank plans by a single criterion."""
        # Sort plans by criterion
        sorted_plans = sorted(
            plans,
            key=lambda p: self._get_criterion_value(
                summaries[p.plan_id], criterion
            ),
        )

        # Get top K plan IDs
        top_plan_ids = [p.plan_id for p in sorted_plans[:max_plans]]

        return RankingResult(
            criterion_id=criterion.id,
            ranked_plan_ids=top_plan_ids,
        )

    def _get_criterion_value(
        self,
        summary: PlanSummary,
        criterion: RankingCriterion,
    ) -> float:
        """Get the value for ranking a plan by a criterion."""
        if criterion.type == RankingCriterionType.MINIMIZE_RECIPE_EXECUTIONS:
            return float(summary.recipe_execution_count)

        elif criterion.type == RankingCriterionType.MINIMIZE_RECIPE_TYPES:
            return float(summary.recipe_type_count)

        elif criterion.type == RankingCriterionType.MINIMIZE_GRAPH_DEPTH:
            return float(summary.graph_depth)

        elif criterion.type == RankingCriterionType.MINIMIZE_MATERIAL_REQUIREMENT:
            if criterion.material_constraint:
                # Find the quantity for this material
                for req in summary.material_requirements:
                    if self._constraints_match(
                        req.constraint, criterion.material_constraint
                    ):
                        return req.quantity
            return float("inf")  # Not found, rank last

        return 0.0

    def _constraints_match(
        self,
        c1: ParameterConstraintSpec,
        c2: ParameterConstraintSpec,
    ) -> bool:
        """Check if two constraints match."""
        return (
            c1.domain == c2.domain
            and c1.key == c2.key
            and c1.operator == c2.operator
            and c1.value_string == c2.value_string
            and c1.value_number == c2.value_number
            and c1.value_boolean == c2.value_boolean
        )
