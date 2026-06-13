import uuid
import math
import time
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from models.recipe import Recipe
from models.slot import Slot, SlotKind
from models.option import Option
from models.parameter_constraint import ParameterConstraint

from repositories.recipe_repository import RecipeRepository
from repositories.slot_repository import SlotRepository
from repositories.option_repository import OptionRepository
from repositories.parameter_constraint_repository import ParameterConstraintRepository
from repositories.project_repository import ProjectRepository

from domain.planning.output_planner import (
    PlanningRequest,
    PlanningResponse,
    PlanCandidate,
    PlanGraph,
    MaterialRequirementNode,
    RecipeExecutionNode,
    Edge,
    EdgeKind,
    NodeKind,
    MaterialRole,
    ParameterConstraintSpec,
    MaterialConstraintRule,
    ObjectiveScore,
    ObjectiveCriterion,
    CriterionKind,
    FailureReason,
    PlanningDiagnostics,
    DomainPlanningConstraints,
    SearchParameters,
    ObjectiveFunction,
    RankingRequest,
    RankingResult,
    RankingCriterion,
    RankingCriterionType,
)

from services.planning.plan_summary_service import PlanSummaryService
from services.planning.plan_ranking_service import PlanRankingService
from services.planning.planner_memoization_cache import PlannerMemoizationCache


@dataclass
class PlanningState:
    """Runtime state during planning."""
    depth: int = 0
    recursion_stack: List[str] = field(default_factory=list)  # Track requirement signatures for loop detection
    node_counter: int = 0
    graph: PlanGraph = field(default_factory=PlanGraph)
    root_requirements: List[MaterialRequirementNode] = field(default_factory=list)
    blocked_requirements: List[FailureReason] = field(default_factory=list)
    material_costs: Dict[str, float] = field(default_factory=dict)
    recipe_execution_count: int = 0


class PlanningService:
    def __init__(self, db: Session):
        self.db = db
        self.recipe_repo = RecipeRepository(db)
        self.slot_repo = SlotRepository(db)
        self.option_repo = OptionRepository(db)
        self.constraint_repo = ParameterConstraintRepository(db)
        self.project_repo = ProjectRepository(db)
        self.summary_service = PlanSummaryService()
        self.ranking_service = PlanRankingService()
        self.memoization_cache = PlannerMemoizationCache()

    def plan(self, request: PlanningRequest, ranking_request: Optional[RankingRequest] = None) -> PlanningResponse:
        """Generate plan candidates for a target requirement."""
        start_time = time.time()
        
        # Validate project exists
        project = self.project_repo.get_by_id(request.project_id)
        if not project:
            return PlanningResponse(success=False, plans=[])
        
        # Get all recipes in project
        recipes = self.recipe_repo.list_by_project(request.project_id)
        
        # Pre-load recipe structures for efficiency
        recipe_structures = {}
        for recipe in recipes:
            recipe_structures[recipe.id] = self._load_recipe_structure(recipe.id)
        
        # Find candidate plans
        plans = []
        
        # Start with target requirement
        target_node = MaterialRequirementNode(
            id=self._generate_node_id("target"),
            role=MaterialRole.TARGET,
            quantity=request.target.quantity,
            constraints=request.target.constraints
        )
        
        # Search for plans
        self._search_plans(
            target_node=target_node,
            request=request,
            recipe_structures=recipe_structures,
            plans=plans,
            state=PlanningState(),
            parent_node_id=None
        )
        
        # Generate plan IDs
        for i, plan in enumerate(plans):
            plan.plan_id = f"plan_{i:03d}"
        
        # Determine ranking criteria
        ranking_to_use = ranking_request
        if ranking_to_use is None:
            # Use objective function as ranking criteria if available
            if request.objective.criteria:
                ranking_to_use = self._objective_to_ranking(request.objective)
            else:
                # Default: minimize recipe executions
                ranking_to_use = RankingRequest(
                    max_plans_per_criterion=10,
                    criteria=[
                        RankingCriterion(
                            id="default_recipe_executions",
                            type=RankingCriterionType.MINIMIZE_RECIPE_EXECUTIONS
                        )
                    ]
                )
        
        # Rank plans
        rankings, remaining_plan_ids = self.ranking_service.rank_plans(plans, ranking_to_use)
        
        # Return all generated plans (ranking indicates which are top K)
        # max_solutions_returned limits the search, not the final output
        final_plans = plans
        
        # Add diagnostics
        elapsed_ms = (time.time() - start_time) * 1000
        for plan in final_plans:
            plan.diagnostics.search_time_ms = elapsed_ms
        
        return PlanningResponse(
            success=True,
            plans=final_plans,
            rankings=rankings,
            remaining_plan_ids=remaining_plan_ids
        )
    
    def _load_recipe_structure(self, recipe_id: uuid.UUID) -> Dict:
        """Load complete recipe structure."""
        slots = self.slot_repo.list_by_recipe(recipe_id)
        structure = {
            "recipe_id": recipe_id,
            "slots": []
        }
        
        for slot in slots:
            options = self.option_repo.list_by_slot(slot.id)
            slot_data = {
                "id": slot.id,
                "kind": slot.kind,
                "options": []
            }
            
            for option in options:
                constraints = self.constraint_repo.list_by_option(option.id)
                option_data = {
                    "id": option.id,
                    "quantity": option.quantity,
                    "constraints": [
                        self._constraint_to_spec(c) for c in constraints
                    ]
                }
                slot_data["options"].append(option_data)
            
            structure["slots"].append(slot_data)
        
        return structure
    
    def _constraint_to_spec(self, constraint: ParameterConstraint) -> ParameterConstraintSpec:
        """Convert database constraint to runtime spec."""
        return ParameterConstraintSpec(
            domain=constraint.domain,
            key=constraint.key,
            operator=constraint.operator,
            value_string=constraint.value_string,
            value_number=constraint.value_number,
            value_boolean=constraint.value_boolean,
            is_wildcard=constraint.is_wildcard
        )
    
    def _generate_node_id(self, prefix: str) -> str:
        """Generate unique node ID."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    
    def _search_plans(
        self,
        target_node: MaterialRequirementNode,
        request: PlanningRequest,
        recipe_structures: Dict[uuid.UUID, Dict],
        plans: List[PlanCandidate],
        state: PlanningState,
        parent_node_id: Optional[str]
    ) -> bool:
        """Recursively search for plans to satisfy a requirement.
        
        Returns True if the requirement was resolved, False if it could not be.
        """
        # Check recipe depth (recursion_stack not yet pushed)
        if state.depth >= request.domain_constraints.max_recipe_depth:
            return False
        
        # Check recursion depth (recursion_stack not yet pushed)
        if state.depth >= request.search_parameters.max_recursion_depth:
            return False
        
        # Check for loops
        req_signature = self._requirement_signature(target_node)
        if not request.search_parameters.allow_loops:
            if req_signature in state.recursion_stack:
                return False
        state.recursion_stack.append(req_signature)
        
        # Check if requirement matches do-not-expand rule
        if self._matches_constraint_rule(
            target_node.constraints,
            request.domain_constraints.do_not_expand_materials_matching
        ):
            # Emit as external requirement
            external_node = MaterialRequirementNode(
                id=self._generate_node_id("external"),
                role=MaterialRole.EXTERNAL_REQUIREMENT,
                quantity=target_node.quantity,
                constraints=target_node.constraints
            )
            state.graph.nodes.append(external_node)
            state.root_requirements.append(external_node)
            
            # Track cost
            cost_key = self._constraint_key(target_node.constraints)
            state.material_costs[cost_key] = state.material_costs.get(cost_key, 0) + target_node.quantity
            
            # Add edge
            if parent_node_id:
                state.graph.edges.append(Edge(
                    from_node=parent_node_id,
                    to_node=external_node.id,
                    kind=EdgeKind.SATISFIES
                ))
            
            state.recursion_stack.pop()
            return True
        
        # Check if requirement matches forbidden material
        if self._matches_constraint_rule(
            target_node.constraints,
            request.domain_constraints.forbidden_materials_matching
        ):
            state.recursion_stack.pop()
            return False
        
        # Find producer recipes
        producers = self._find_producer_recipes(
            target_node.constraints,
            recipe_structures,
            request.domain_constraints.forbidden_recipe_ids
        )
        
        if not producers:
            # No producer found - mark target node as root requirement
            target_node.role = MaterialRole.ROOT_REQUIREMENT
            state.graph.nodes.append(target_node)
            state.root_requirements.append(target_node)
            
            # Track cost
            cost_key = self._constraint_key(target_node.constraints)
            state.material_costs[cost_key] = state.material_costs.get(cost_key, 0) + target_node.quantity
            
            # Add edge from parent to this root requirement
            if parent_node_id:
                state.graph.edges.append(Edge(
                    from_node=parent_node_id,
                    to_node=target_node.id,
                    kind=EdgeKind.SATISFIES
                ))
            
            state.recursion_stack.pop()
            return True
        
        # Limit branch width
        max_width = request.search_parameters.max_branch_width
        producers = producers[:max_width]
        
        any_producer_succeeded = False
        
        # Try each producer
        for recipe_id, option in producers:
            # Clone state for this branch
            branch_state = self._clone_state(state)
            
            # Create recipe execution node
            recipe_exec_node = RecipeExecutionNode(
                id=self._generate_node_id("recipe_exec"),
                recipe_id=recipe_id,
                execution_count=1  # Will calculate based on quantity
            )
            branch_state.graph.nodes.append(recipe_exec_node)
            branch_state.recipe_execution_count += 1
            
            # Calculate execution count based on quantity
            produced_quantity = option["quantity"]
            if produced_quantity > 0:
                recipe_exec_node.execution_count = math.ceil(target_node.quantity / produced_quantity)
            
            # Add edge from recipe to parent (satisfies the requirement)
            if parent_node_id:
                branch_state.graph.edges.append(Edge(
                    from_node=recipe_exec_node.id,
                    to_node=parent_node_id,
                    kind=EdgeKind.SATISFIES
                ))
            
            # Create produced material node
            produced_node = MaterialRequirementNode(
                id=self._generate_node_id("produced"),
                role=MaterialRole.PRODUCED,
                quantity=target_node.quantity,
                constraints=target_node.constraints
            )
            branch_state.graph.nodes.append(produced_node)
            branch_state.graph.edges.append(Edge(
                from_node=recipe_exec_node.id,
                to_node=produced_node.id,
                kind=EdgeKind.PRODUCES
            ))
            
            # Get recipe structure
            recipe_structure = recipe_structures[recipe_id]
            
            # Process all consumes/requires slots - all must succeed for this branch to succeed
            slot_success = True
            plans_before = len(plans)
            for slot in recipe_structure["slots"]:
                if not slot_success:
                    break
                if slot["kind"] in [SlotKind.CONSUMES, SlotKind.REQUIRES]:
                    edge_kind = EdgeKind.CONSUMES if slot["kind"] == SlotKind.CONSUMES else EdgeKind.REQUIRES
                    
                    for slot_option in slot["options"]:
                        # Scale quantity by execution count
                        scaled_quantity = slot_option["quantity"] * recipe_exec_node.execution_count
                        
                        # Create sub-requirement
                        sub_req_node = MaterialRequirementNode(
                            id=self._generate_node_id("sub_req"),
                            role=MaterialRole.INTERMEDIATE,
                            quantity=scaled_quantity,
                            constraints=slot_option["constraints"]
                        )
                        branch_state.graph.nodes.append(sub_req_node)
                        
                        # Add edge from material to recipe (more intuitive flow)
                        branch_state.graph.edges.append(Edge(
                            from_node=sub_req_node.id,
                            to_node=recipe_exec_node.id,
                            kind=edge_kind
                        ))
                        
                        # Recursively resolve - failure propagates up
                        branch_state.depth += 1
                        resolved = self._search_plans(
                            target_node=sub_req_node,
                            request=request,
                            recipe_structures=recipe_structures,
                            plans=plans,
                            state=branch_state,
                            parent_node_id=recipe_exec_node.id
                        )
                        branch_state.depth -= 1
                        
                        if not resolved:
                            slot_success = False
                            break
            
            if slot_success:
                any_producer_succeeded = True
                # Always add plan at this level (after all recursive calls complete)
                # Collect all ROOT_REQUIREMENT and EXTERNAL_REQUIREMENT nodes from the graph
                root_req_nodes = [n for n in branch_state.graph.nodes if isinstance(n, MaterialRequirementNode) and n.role in (MaterialRole.ROOT_REQUIREMENT, MaterialRole.EXTERNAL_REQUIREMENT)]
                plan = PlanCandidate(
                    success=True,
                    plan_id=self._generate_node_id("plan"),
                    graph=branch_state.graph,
                    root_requirements=root_req_nodes,
                    blocked_requirements=branch_state.blocked_requirements,
                    score=ObjectiveScore(
                        material_costs=branch_state.material_costs,
                        recipe_count=branch_state.recipe_execution_count
                    )
                )
                plans.append(plan)
        
        state.recursion_stack.pop()
        return any_producer_succeeded
    
    def _find_producer_recipes(
        self,
        constraints: List[ParameterConstraintSpec],
        recipe_structures: Dict[uuid.UUID, Dict],
        forbidden_recipe_ids: List[uuid.UUID]
    ) -> List[Tuple[uuid.UUID, Dict]]:
        """Find recipes that can produce materials matching constraints."""
        producers = []
        
        for recipe_id, structure in recipe_structures.items():
            if recipe_id in forbidden_recipe_ids:
                continue
            
            # Check if recipe has PRODUCES slots
            for slot in structure["slots"]:
                if slot["kind"] == SlotKind.PRODUCES:
                    for option in slot["options"]:
                        # Check if option constraints match target constraints
                        if self._constraints_match(constraints, option["constraints"]):
                            producers.append((recipe_id, option))
                            break  # One matching option is enough
        
        # Sort deterministically by recipe_id
        producers.sort(key=lambda x: str(x[0]))
        
        return producers
    
    def _constraints_match(
        self,
        target_constraints: List[ParameterConstraintSpec],
        option_constraints: List[ParameterConstraintSpec]
    ) -> bool:
        """Check if option constraints can satisfy target constraints."""
        # For now, simple check: all target constraints must be satisfied by option
        for target in target_constraints:
            matched = False
            for opt in option_constraints:
                if (target.domain == opt.domain and
                    target.key == opt.key and
                    target.operator == opt.operator and
                    target.value_string == opt.value_string and
                    target.value_number == opt.value_number and
                    target.value_boolean == opt.value_boolean):
                    matched = True
                    break
            if not matched:
                return False
        return True
    
    def _matches_constraint_rule(
        self,
        constraints: List[ParameterConstraintSpec],
        rules: List[MaterialConstraintRule]
    ) -> bool:
        """Check if constraints match any rule."""
        for rule in rules:
            if self._constraints_match(constraints, rule.constraints):
                return True
        return False
    
    def _requirement_signature(self, node: MaterialRequirementNode) -> str:
        """Generate signature for loop detection."""
        key = self._constraint_key(node.constraints)
        return f"{key}:{node.quantity}"
    
    def _constraint_key(self, constraints: List[ParameterConstraintSpec]) -> str:
        """Generate a key from constraints for cost tracking."""
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
    
    def _clone_state(self, state: PlanningState) -> PlanningState:
        """Clone planning state for branching."""
        return PlanningState(
            depth=state.depth,
            recursion_stack=list(state.recursion_stack),
            node_counter=state.node_counter,
            graph=PlanGraph(
                nodes=list(state.graph.nodes),
                edges=list(state.graph.edges)
            ),
            root_requirements=list(state.root_requirements),
            blocked_requirements=list(state.blocked_requirements),
            material_costs=dict(state.material_costs),
            recipe_execution_count=state.recipe_execution_count
        )
    
    def _rank_plans(
        self,
        plans: List[PlanCandidate],
        objective: ObjectiveFunction
    ) -> List[PlanCandidate]:
        """Rank plans by objective function."""
        # Calculate objective tuple for each plan
        for plan in plans:
            plan.score.objective_tuple = self._calculate_objective_tuple(plan, objective)
        
        # Sort by objective tuple (lexicographic)
        plans.sort(key=lambda p: p.score.objective_tuple)
        
        return plans
    
    def _calculate_objective_tuple(
        self,
        plan: PlanCandidate,
        objective: ObjectiveFunction
    ) -> List[float]:
        """Calculate objective tuple for a plan."""
        tuple_values = []
        
        for criterion in objective.criteria:
            if criterion.kind == CriterionKind.MATERIAL:
                # Find cost for this material
                cost_key = self._constraint_key(criterion.constraints)
                cost = plan.score.material_costs.get(cost_key, 0.0)
                tuple_values.append(cost)
            elif criterion.kind == CriterionKind.RECIPE_COUNT:
                tuple_values.append(float(plan.score.recipe_count))
        
        return tuple_values
    
    def _objective_to_ranking(self, objective: ObjectiveFunction) -> RankingRequest:
        """Convert objective function to ranking request."""
        criteria = []
        for i, obj_criterion in enumerate(objective.criteria):
            if obj_criterion.kind == CriterionKind.MATERIAL:
                criteria.append(
                    RankingCriterion(
                        id=f"material_{i}",
                        type=RankingCriterionType.MINIMIZE_MATERIAL_REQUIREMENT,
                        material_constraint=obj_criterion.constraints[0] if obj_criterion.constraints else None
                    )
                )
            elif obj_criterion.kind == CriterionKind.RECIPE_COUNT:
                criteria.append(
                    RankingCriterion(
                        id=f"recipe_count_{i}",
                        type=RankingCriterionType.MINIMIZE_RECIPE_EXECUTIONS
                    )
                )
            elif obj_criterion.kind == CriterionKind.RECIPE_TYPES:
                criteria.append(
                    RankingCriterion(
                        id=f"recipe_types_{i}",
                        type=RankingCriterionType.MINIMIZE_RECIPE_TYPES
                    )
                )
            elif obj_criterion.kind == CriterionKind.GRAPH_DEPTH:
                criteria.append(
                    RankingCriterion(
                        id=f"graph_depth_{i}",
                        type=RankingCriterionType.MINIMIZE_GRAPH_DEPTH
                    )
                )
        
        return RankingRequest(
            max_plans_per_criterion=10,
            criteria=criteria
        )
    
    @staticmethod
    def print_plan_graph(plan_response: dict) -> None:
        """Pretty-print a planning response graph for debugging."""
        import json
        print("\n" + "=" * 60)
        print("PLAN GRAPH OUTPUT")
        print("=" * 60)
        print(f"Success: {plan_response.get('success')}")
        print(f"Number of plans: {len(plan_response.get('plans', []))}")
        
        for i, plan in enumerate(plan_response.get('plans', []), 1):
            print(f"\n--- Plan {i}: {plan.get('plan_id')} ---")
            print(f"Success: {plan.get('success')}")
            print(f"Blocked requirements: {len(plan.get('blocked_requirements', []))}")
            
            if plan.get('blocked_requirements'):
                print("  Blocked:")
                for br in plan['blocked_requirements']:
                    print(f"    - {br['requirement_id']}: {br['reason']}")
            
            graph = plan.get('graph', {})
            nodes = graph.get('nodes', [])
            edges = graph.get('edges', [])
            
            print(f"\n  Nodes ({len(nodes)}):")
            for node in nodes:
                kind = node.get('kind')
                if kind == 'recipe_execution':
                    print(f"    [{node['id']}] Recipe {node.get('recipe_id')} (exec_count={node.get('execution_count')})")
                elif kind == 'material_requirement':
                    role = node.get('role')
                    qty = node.get('quantity')
                    constraints = node.get('constraints', [])
                    cons_str = ', '.join([f"{c['key']}={c.get('value_string', c.get('value_number', c.get('value_boolean')))}" for c in constraints])
                    print(f"    [{node['id']}] {role} (qty={qty}, {cons_str})")
            
            print(f"\n  Edges ({len(edges)}):")
            for edge in edges:
                print(f"    {edge['from_node']} --[{edge['kind']}]--> {edge['to_node']}")
            
            print(f"\n  Root requirements ({len(plan.get('root_requirements', []))}):")
            for req in plan.get('root_requirements', []):
                constraints = req.get('constraints', [])
                cons_str = ', '.join([f"{c['key']}={c.get('value_string', c.get('value_number', c.get('value_boolean')))}" for c in constraints])
                print(f"    [{req['id']}] {req.get('role')} (qty={req.get('quantity')}, {cons_str})")
            
            score = plan.get('score', {})
            print(f"\n  Score: material_costs={score.get('material_costs')}, recipe_count={score.get('recipe_count')}")
            
            diag = plan.get('diagnostics', {})
            print(f"  Diagnostics: {diag.get('search_time_ms', 0):.2f}ms, branches_pruned={diag.get('branches_pruned', 0)}")
        
        print("\n" + "=" * 60 + "\n")
