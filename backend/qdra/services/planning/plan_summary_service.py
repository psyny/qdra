from typing import List, Dict, Set
from collections import Counter

from domain.planning.output_planner import (
    PlanCandidate,
    PlanSummary,
    MaterialRequirementSummary,
    ParameterConstraintSpec,
    RecipeExecutionNode,
    MaterialRequirementNode,
    MaterialRole,
)


class PlanSummaryService:
    """Service for computing plan summary metrics used in ranking."""

    def compute_summary(self, plan: PlanCandidate) -> PlanSummary:
        """Compute summary metrics for a plan."""
        recipe_execution_count = self._count_recipe_executions(plan)
        recipe_type_count = self._count_recipe_types(plan)
        graph_depth = self._compute_graph_depth(plan)
        material_requirements = self._aggregate_material_requirements(plan)

        return PlanSummary(
            plan_id=plan.plan_id,
            recipe_execution_count=recipe_execution_count,
            recipe_type_count=recipe_type_count,
            graph_depth=graph_depth,
            material_requirements=material_requirements,
        )

    def _count_recipe_executions(self, plan: PlanCandidate) -> int:
        """Count total recipe executions in the plan."""
        count = 0
        for node in plan.graph.nodes:
            if isinstance(node, RecipeExecutionNode):
                count += node.execution_count
        return count

    def _count_recipe_types(self, plan: PlanCandidate) -> int:
        """Count unique recipe types in the plan."""
        recipe_ids = set()
        for node in plan.graph.nodes:
            if isinstance(node, RecipeExecutionNode):
                recipe_ids.add(node.recipe_id)
        return len(recipe_ids)

    def _compute_graph_depth(self, plan: PlanCandidate) -> int:
        """Compute the maximum depth of the plan graph."""
        # Build adjacency list
        edges_by_node: Dict[str, List[str]] = {}
        for edge in plan.graph.edges:
            if edge.from_node not in edges_by_node:
                edges_by_node[edge.from_node] = []
            edges_by_node[edge.from_node].append(edge.to_node)

        # Find target node (node with no incoming edges)
        all_nodes = {node.id for node in plan.graph.nodes}
        target_nodes = set()
        for edge in plan.graph.edges:
            target_nodes.discard(edge.to_node)
        target_nodes = all_nodes - target_nodes

        if not target_nodes:
            return 0

        # BFS to find max depth
        max_depth = 0
        for target in target_nodes:
            depth = self._bfs_depth(target, edges_by_node)
            max_depth = max(max_depth, depth)

        return max_depth

    def _bfs_depth(self, start: str, edges: Dict[str, List[str]]) -> int:
        """BFS to compute depth from start node."""
        visited = {start}
        queue = [(start, 0)]
        max_depth = 0

        while queue:
            node, depth = queue.pop(0)
            max_depth = max(max_depth, depth)

            if node in edges:
                for neighbor in edges[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, depth + 1))

        return max_depth

    def _aggregate_material_requirements(self, plan: PlanCandidate) -> List[MaterialRequirementSummary]:
        """Aggregate material requirements from root requirements."""
        material_totals: Dict[str, float] = {}
        constraint_map: Dict[str, ParameterConstraintSpec] = {}

        for req in plan.root_requirements:
            if req.role in [MaterialRole.ROOT_REQUIREMENT, MaterialRole.EXTERNAL_REQUIREMENT]:
                # Generate a key for the constraint
                key = self._constraint_key(req.constraints)
                material_totals[key] = material_totals.get(key, 0) + req.quantity
                constraint_map[key] = req.constraints[0] if req.constraints else None

        summaries = []
        for key, quantity in material_totals.items():
            constraint = constraint_map.get(key)
            if constraint:
                summaries.append(
                    MaterialRequirementSummary(
                        constraint=constraint,
                        quantity=quantity,
                    )
                )

        return summaries

    def _constraint_key(self, constraints: List[ParameterConstraintSpec]) -> str:
        """Generate a key from constraints for aggregation."""
        parts = []
        for c in constraints:
            part = f"{c.domain}.{c.key}"
            if c.value_string:
                part += f"={c.value_string}"
            elif c.value_number is not None:
                part += f"={c.value_number}"
            elif c.value_boolean is not None:
                part += f"={c.value_boolean}"
            parts.append(part)
        return ",".join(sorted(parts))
