import uuid
import hashlib
import json
from typing import Dict, List, Optional

from domain.planning.output_planner import (
    MemoizationCacheKey,
    MemoizedPlanningResult,
    PlanCandidate,
    ParameterConstraintSpec,
    MaterialConstraintRule,
    DomainPlanningConstraints,
)


class PlannerMemoizationCache:
    """In-memory cache for planning subproblems."""

    def __init__(self):
        self._cache: Dict[str, MemoizedPlanningResult] = {}

    def get(self, key: MemoizationCacheKey) -> Optional[MemoizedPlanningResult]:
        """Retrieve cached result for a subproblem."""
        cache_key = self._make_cache_key(key)
        return self._cache.get(cache_key)

    def put(self, key: MemoizationCacheKey, result: MemoizedPlanningResult) -> None:
        """Store result for a subproblem."""
        cache_key = self._make_cache_key(key)
        self._cache[cache_key] = result

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()

    def _make_cache_key(self, key: MemoizationCacheKey) -> str:
        """Generate a hash-based cache key from the memoization key."""
        # Convert all components to a stable string representation
        key_parts = [
            self._serialize_constraints(key.target_constraints),
            str(key.target_quantity),
            self._serialize_domain_constraints(key.domain_constraints),
            str(key.search_depth_remaining),
            self._serialize_constraint_rules(key.forbidden_recipes),
            self._serialize_constraint_rules(key.forbidden_materials),
            self._serialize_constraint_rules(key.do_not_expand_materials),
            str(key.allow_loops),
        ]

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _serialize_constraints(self, constraints: List[ParameterConstraintSpec]) -> str:
        """Serialize constraints to a stable string."""
        sorted_constraints = sorted(
            constraints,
            key=lambda c: (c.domain, c.key, c.operator),
        )
        return json.dumps(
            [
                {
                    "domain": c.domain,
                    "key": c.key,
                    "operator": c.operator,
                    "value_string": c.value_string,
                    "value_number": c.value_number,
                    "value_boolean": c.value_boolean,
                    "is_wildcard": c.is_wildcard,
                }
                for c in sorted_constraints
            ]
        )

    def _serialize_domain_constraints(self, constraints: DomainPlanningConstraints) -> str:
        """Serialize domain constraints to a stable string."""
        return json.dumps(
            {
                "max_recipe_depth": constraints.max_recipe_depth,
                "forbidden_recipe_matching": self._serialize_constraint_rules(constraints.forbidden_recipe_matching),
            }
        )

    def _serialize_uuid_list(self, uuids: List[uuid.UUID]) -> str:
        """Serialize a list of UUIDs to a stable string."""
        return ",".join(sorted(str(id) for id in uuids))

    def _serialize_constraint_rules(self, rules: List[MaterialConstraintRule]) -> str:
        """Serialize constraint rules to a stable string."""
        sorted_rules = sorted(
            rules,
            key=lambda r: self._serialize_constraints(r.constraints),
        )
        return json.dumps(
            [self._serialize_constraints(rule.constraints) for rule in sorted_rules]
        )

    def clone_subplan_with_new_ids(
        self,
        subplan: PlanCandidate,
        id_prefix: str,
    ) -> PlanCandidate:
        """Clone a subplan with new node IDs to avoid collisions."""
        # Create ID mapping
        id_map: Dict[str, str] = {}
        for node in subplan.graph.nodes:
            old_id = node.id
            new_id = f"{id_prefix}_{old_id}"
            id_map[old_id] = new_id

        # Clone nodes with new IDs
        from domain.planning.output_planner import (
            MaterialRequirementNode,
            RecipeExecutionNode,
            PlanGraph,
            Edge,
        )

        new_nodes = []
        for node in subplan.graph.nodes:
            if isinstance(node, MaterialRequirementNode):
                new_node = MaterialRequirementNode(
                    id=id_map[node.id],
                    kind=node.kind,
                    role=node.role,
                    quantity=node.quantity,
                    constraints=node.constraints,
                )
            elif isinstance(node, RecipeExecutionNode):
                new_node = RecipeExecutionNode(
                    id=id_map[node.id],
                    recipe_id=node.recipe_id,
                    kind=node.kind,
                    execution_count=node.execution_count,
                )
            else:
                new_node = node
            new_nodes.append(new_node)

        # Clone edges with new IDs
        new_edges = []
        for edge in subplan.graph.edges:
            new_edge = Edge(
                from_node=id_map[edge.from_node],
                to_node=id_map[edge.to_node],
                kind=edge.kind,
            )
            new_edges.append(new_edge)

        # Clone root requirements with new IDs
        new_root_requirements = []
        for req in subplan.root_requirements:
            new_req = MaterialRequirementNode(
                id=id_map[req.id],
                kind=req.kind,
                role=req.role,
                quantity=req.quantity,
                constraints=req.constraints,
            )
            new_root_requirements.append(new_req)

        # Create new plan
        new_plan = PlanCandidate(
            success=subplan.success,
            plan_id=f"{id_prefix}_plan",
            graph=PlanGraph(nodes=new_nodes, edges=new_edges),
            root_requirements=new_root_requirements,
            blocked_requirements=subplan.blocked_requirements,
            score=subplan.score,
            diagnostics=subplan.diagnostics,
        )

        return new_plan
