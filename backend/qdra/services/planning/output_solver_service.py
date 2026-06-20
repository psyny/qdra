import copy
import math
import re
import uuid
from collections import deque
from itertools import chain
from typing import Any, Deque, Dict, Iterable, List, Optional, Set, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from cachetools import TTLCache

from models.entity import Entity
from repositories.entity_repository import EntityRepository
from repositories.entity_parameter_repository import EntityParameterRepository
from repositories.project_repository import ProjectRepository
from services.recipe_evaluation_service import RecipeEvaluationService
from services.constraint_resolution_service import ConstraintResolutionService
from qdra.infrastructure.cache.cache_service import CacheService

from domain.planning.output_solver_domain import (
    MaterialNode, RecipeExecNode, MaterialEdge, RecipeEdge,
    MaterialNodeType, RecipeEdgeType, ConstraintSpec, ConstraintRule,
    SolvedPlan, SolverRequest, SolverResponse,
    SYSTEM_VARIABLE_NAMES,
    Entities, EntityData, DiscardedPlansStats,
)


@dataclass
class _State:
    material_nodes: Dict[str, MaterialNode]
    recipe_nodes: Dict[str, RecipeExecNode]
    material_edges: List[MaterialEdge]
    recipe_edges: List[RecipeEdge]
    needs_queue: Deque[str]
    recipe_depth: int = 0
    _counter: int = 0

    def next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter:04d}"

    def clone(self) -> "_State":
        return _State(
            material_nodes={k: copy.copy(v) for k, v in self.material_nodes.items()},
            recipe_nodes=dict(self.recipe_nodes),
            material_edges=list(self.material_edges),
            recipe_edges=list(self.recipe_edges),
            needs_queue=deque(self.needs_queue),
            recipe_depth=self.recipe_depth,
            _counter=self._counter,
        )




def validate_formula(formula: str, variable_names: Set[str]) -> None:
    """Validate a score formula string. Raises ValueError if invalid."""
    identifiers = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', formula))
    unknown = identifiers - variable_names
    if unknown:
        raise ValueError(f"Unknown variables in formula '{formula}': {unknown}")
    test_vars = {name: 1.0 for name in variable_names}
    try:
        result = eval(formula, {"__builtins__": {}}, test_vars)
        float(result)
    except ZeroDivisionError:
        pass
    except Exception as e:
        raise ValueError(f"Invalid formula '{formula}': {e}")


class OutputSolverService:
    def __init__(self, db: Session):
        self.db = db
        self.entity_repo = EntityRepository(db, CacheService())
        self.entity_param_repo = EntityParameterRepository(db)
        self.project_repo = ProjectRepository(db)
        self.recipe_eval_service = RecipeEvaluationService(db)
        self.constraint_resolution_service = ConstraintResolutionService(db)
        # Entity parameters cache (only cache not moved to service level)
        self.cache = TTLCache(maxsize=10000, ttl=60*5)

    def _cache_get_or_set(self, key: str, loader):
        if key not in self.cache:
            self.cache[key] = loader()
        return self.cache[key]

    def _list_entity_params_cached(self, entity_id: uuid.UUID) -> List:
        return self._cache_get_or_set(
            f"entity_params_{entity_id}",
            lambda: self.entity_param_repo.list_by_entity(entity_id),
        )

    def _get_recipes_for_material(self, material_id: uuid.UUID, project_id: uuid.UUID) -> dict:
        """Get recipes that can consume/produce/require this material (cached at service level)."""
        return self.recipe_eval_service.find_recipes_for_material(material_id, project_id)

    def _get_materials_for_recipe(self, recipe_id: uuid.UUID, project_id: uuid.UUID) -> dict:
        """Get materials that match each slot of this recipe (cached at service level)."""
        return self.recipe_eval_service.find_materials_for_recipe_slots(recipe_id, project_id)

    def _find_materials_by_constraints(self, constraints: List[ConstraintSpec], project_id: uuid.UUID) -> List[uuid.UUID]:
        """Find materials in the project that match the given constraints (delegated to service)."""
        return self.constraint_resolution_service.find_materials_by_constraints(constraints, project_id)

    def _find_recipes_by_constraints(self, constraints: List[ConstraintSpec], project_id: uuid.UUID) -> List[uuid.UUID]:
        """Find recipes in the project that match the given constraints (delegated to service)."""
        return self.constraint_resolution_service.find_recipes_by_constraints(constraints, project_id)

    def _preload_constraint_materials(self, project_id: uuid.UUID, constraint_rules: List[ConstraintRule]) -> Set[uuid.UUID]:
        """Pre-load all material IDs matching the given constraint rules."""
        matching_ids = set()
        
        for rule in constraint_rules:
            material_ids = self._find_materials_by_constraints(rule.constraints, project_id)
            matching_ids.update(material_ids)
        
        return matching_ids

    def _preload_constraint_recipes(self, project_id: uuid.UUID, constraint_rules: List[ConstraintRule]) -> Set[uuid.UUID]:
        """Pre-load all recipe IDs matching the given constraint rules (returns union for forbidden)."""
        matching_ids = set()
        
        for rule in constraint_rules:
            recipe_ids = self._find_recipes_by_constraints(rule.constraints, project_id)
            matching_ids.update(recipe_ids)
        
        return matching_ids

    def _preload_constraint_recipes_by_rule(self, project_id: uuid.UUID, constraint_rules: List[ConstraintRule]) -> Dict[int, Set[uuid.UUID]]:
        """Pre-load recipe IDs per rule for required recipes (returns dict mapping rule index to IDs)."""
        matching_by_rule = {}
        
        for i, rule in enumerate(constraint_rules):
            recipe_ids = self._find_recipes_by_constraints(rule.constraints, project_id)
            matching_by_rule[i] = set(recipe_ids)
        
        return matching_by_rule

    def solve(self, request: SolverRequest) -> SolverResponse:
        if not self.project_repo.get_by_id(request.project_id):
            return SolverResponse(success=False)

        if request.score_rules and request.score_rules.score_formulas:
            system_names = set(SYSTEM_VARIABLE_NAMES)
            user_names = {v.name for v in request.score_rules.user_variables}
            all_names = system_names | user_names
            for fdef in request.score_rules.score_formulas:
                validate_formula(fdef.formula, all_names)

        recipes = self.entity_repo.list_by_project(request.project_id, kind="recipe")

        # Pre-load material ID sets for constraint rules
        forbidden_materials_ids = self._preload_constraint_materials(
            request.project_id, request.domain_constraints.forbidden_materials_matching
        )
        required_materials_ids = self._preload_constraint_materials(
            request.project_id, request.domain_constraints.required_materials_matching
        )
        do_not_expand_materials_ids = self._preload_constraint_materials(
            request.project_id, request.domain_constraints.do_not_expand_materials_matching
        )

        # Pre-load recipe ID sets for constraint rules
        forbidden_recipes_ids = self._preload_constraint_recipes(
            request.project_id, request.domain_constraints.forbidden_recipe_matching
        )
        required_recipes_by_rule = self._preload_constraint_recipes_by_rule(
            request.project_id, request.domain_constraints.required_recipe_matching
        )

        # Pre-load material ID sets for user variable constraints
        user_var_material_ids: Dict[str, Set[uuid.UUID]] = {}
        if request.score_rules:
            for var_def in request.score_rules.user_variables:
                if var_def.variable_type == "material":
                    # Convert constraint options to ConstraintRule format for pre-loading
                    constraint_rules = [ConstraintRule(constraints=option) for option in var_def.constraints]
                    var_material_ids = self._preload_constraint_materials(request.project_id, constraint_rules)
                    user_var_material_ids[var_def.name] = var_material_ids

        recipe_params: Dict[str, List[ConstraintSpec]] = {}
        # Load recipe params if needed for score rules, recipe target matching, forbidden_recipe_matching, OR required_recipe_matching
        if request.target.target_type == "recipe" or (request.score_rules and any(
            v.variable_type == "recipe" for v in request.score_rules.user_variables
        )) or request.domain_constraints.forbidden_recipe_matching or request.domain_constraints.required_recipe_matching:
            recipe_params = self._load_recipe_params([r.id for r in recipes])

        # Initialize state based on target type (material or recipe)
        if request.target.target_type == "recipe":
            initial_states = self._initialize_recipe_target(request, recipe_params)
        else:
            initial_states = self._initialize_material_target(request)

        plans: List[SolvedPlan] = []
        seen_fps: Set[str] = set()
        discarded_stats = DiscardedPlansStats()
        
        # Explore from each initial state (for material targets, there may be multiple matching materials; for recipe targets, there may be multiple matching recipes)
        for initial in initial_states:
            self._explore(initial, request, plans, seen_fps, frozenset(), recipe_params, discarded_stats,
                         forbidden_materials_ids, required_materials_ids, do_not_expand_materials_ids, user_var_material_ids,
                         forbidden_recipes_ids, required_recipes_by_rule)

        for i, plan in enumerate(plans):
            plan.plan_id = f"plan_{i:03d}"
            self._tag_nodes(plan)

        entities = self._collect_entities(plans, request.project_id)
        return SolverResponse(success=True, plans=plans, entities=entities, discarded_plans_stats=discarded_stats)

    @staticmethod
    def _build_adjacency(
        material_edges: List[MaterialEdge],
        recipe_edges: List[RecipeEdge],
    ) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        outgoing: Dict[str, List[str]] = {}
        incoming: Dict[str, List[str]] = {}

        for edge in chain(material_edges, recipe_edges):
            outgoing.setdefault(edge.from_node_id, []).append(edge.to_node_id)
            incoming.setdefault(edge.to_node_id, []).append(edge.from_node_id)

        return outgoing, incoming

    @staticmethod
    def _apply_node_tags(
        material_nodes: Dict[str, MaterialNode],
        recipe_nodes: Dict[str, RecipeExecNode],
        material_edges: List[MaterialEdge],
        recipe_edges: List[RecipeEdge],
    ) -> None:
        outgoing, incoming = OutputSolverService._build_adjacency(material_edges, recipe_edges)

        for node in material_nodes.values():
            tags: Set[str] = set()
            if node.produced_qty > node.consumed_qty:
                tags.add("excess")
            if not outgoing.get(node.id):
                tags.add("leaf")
            if not incoming.get(node.id):
                tags.add("root")
            node.tags = list(tags)

        for node in recipe_nodes.values():
            tags: Set[str] = set()
            if not incoming.get(node.id):
                tags.add("root")
            node.tags = list(tags)

    def _tag_state_nodes(self, state: "_State") -> None:
        self._apply_node_tags(
            state.material_nodes,
            state.recipe_nodes,
            state.material_edges,
            state.recipe_edges,
        )

    def _tag_nodes(self, plan: SolvedPlan) -> None:
        material_nodes = {
            node.id: node for node in plan.graph_nodes if isinstance(node, MaterialNode)
        }
        recipe_nodes = {
            node.id: node for node in plan.graph_nodes if isinstance(node, RecipeExecNode)
        }
        self._apply_node_tags(material_nodes, recipe_nodes, plan.material_edges, plan.recipe_edges)

    def _explore(self, state, request, plans, seen_fps, ancestor_sigs, recipe_params, discarded_stats,
                 forbidden_materials_ids, required_materials_ids, do_not_expand_materials_ids, user_var_material_ids,
                 forbidden_recipes_ids, required_recipes_by_rule):
        if len(plans) >= request.search_parameters.max_solutions_returned:
            discarded_stats.max_solutions_returned += 1
            return

        current_id = None
        while state.needs_queue:
            nid = state.needs_queue.popleft()
            node = state.material_nodes.get(nid)
            if node is not None and node.produced_qty < node.consumed_qty:
                current_id = nid
                break

        if current_id is None:
            self._emit_plan(state, plans, seen_fps, request.score_rules, recipe_params, request.search_parameters.optimization_level,
                           request.domain_constraints, required_materials_ids, user_var_material_ids, required_recipes_by_rule)
            return

        current = state.material_nodes[current_id]

        # Loop detection: only prevent if the same NODE is in the current path, not just same signature
        # This allows diamond dependencies (same material needed by different branches)
        if not request.search_parameters.allow_loops and current_id in ancestor_sigs:
            discarded_stats.loops += 1
            return
        if state.recipe_depth >= request.domain_constraints.max_recipe_depth:
            discarded_stats.max_recipe_depth += 1
            return
        if state.recipe_depth >= request.search_parameters.max_recursion_depth:
            discarded_stats.max_recursion_depth += 1
            return

        surplus_id = self._find_surplus(state, current)
        if surplus_id is not None:
            branch = state.clone()
            self._apply_surplus(branch, surplus_id, current_id)
            self._explore(branch, request, plans, seen_fps, ancestor_sigs, recipe_params, discarded_stats,
                         forbidden_materials_ids, required_materials_ids, do_not_expand_materials_ids, user_var_material_ids,
                         forbidden_recipes_ids, required_recipes_by_rule)
            return

        # Check if material is in do_not_expand set
        if current.material_id and current.material_id in do_not_expand_materials_ids:
            discarded_stats.do_not_expand_materials += 1
            self._explore(state, request, plans, seen_fps, ancestor_sigs, recipe_params, discarded_stats,
                         forbidden_materials_ids, required_materials_ids, do_not_expand_materials_ids, user_var_material_ids,
                         forbidden_recipes_ids, required_recipes_by_rule)
            return

        # Check if material is in forbidden set
        if current.material_id and current.material_id in forbidden_materials_ids:
            discarded_stats.forbidden_materials += 1
            return

        # Find producers for this material
        if current.material_id is None:
            # Material not yet resolved - can't find producers
            discarded_stats.no_producers_found += 1
            self._explore(state, request, plans, seen_fps, ancestor_sigs, recipe_params, discarded_stats,
                         forbidden_materials_ids, required_materials_ids, do_not_expand_materials_ids, user_var_material_ids,
                         forbidden_recipes_ids, required_recipes_by_rule)
            return

        producers = self._find_producers(
            current.material_id, request.project_id,
            forbidden_recipes_ids,
        )

        if not producers:
            discarded_stats.no_producers_found += 1
            self._explore(state, request, plans, seen_fps, ancestor_sigs, recipe_params, discarded_stats,
                         forbidden_materials_ids, required_materials_ids, do_not_expand_materials_ids, user_var_material_ids,
                         forbidden_recipes_ids, required_recipes_by_rule)
            return

        producers = producers[: request.search_parameters.max_branch_width]
        new_ancestors = ancestor_sigs | {current_id}

        for recipe_id, produces_option in producers:
            if len(plans) >= request.search_parameters.max_solutions_returned:
                discarded_stats.max_solutions_returned += 1
                return
            branch = state.clone()
            self._apply_recipe(branch, current_id, recipe_id, produces_option, request)
            branch.recipe_depth += 1
            self._explore(branch, request, plans, seen_fps, new_ancestors, recipe_params, discarded_stats,
                         forbidden_materials_ids, required_materials_ids, do_not_expand_materials_ids, user_var_material_ids,
                         forbidden_recipes_ids, required_recipes_by_rule)

    def _add_recipe_material_nodes(
        self,
        state: "_State",
        recipe_node_id: str,
        recipe_materials: dict,
        exec_count: float,
        rank: int,
        output_type: MaterialNodeType,
        target_need_id: Optional[str] = None,
    ) -> List[str]:
        """Add material nodes and recipe edges for one recipe execution.

        The recipe-evaluation service returns slots grouped by kind. Current solver
        semantics still pick the first matching material for each option, exactly as
        before; this helper only removes the repeated produces/consumes/requires
        construction code.
        """
        new_inputs: List[str] = []
        need = state.material_nodes.get(target_need_id) if target_need_id else None

        def first_matching_material_id(option: dict) -> Optional[uuid.UUID]:
            matches = option.get("matching_material_ids") or []
            return uuid.UUID(matches[0]) if matches else None

        for slot in recipe_materials["produces"]:
            for opt in slot["options"]:
                material_id = first_matching_material_id(opt)
                if material_id is None:
                    continue

                scaled_qty = opt["quantity"] * exec_count
                output_id = state.next_id("O")
                output_node = MaterialNode(
                    id=output_id,
                    material_id=material_id,
                    produced_qty=scaled_qty,
                    consumed_qty=0.0,
                    type=output_type,
                    rank=rank,
                )
                state.material_nodes[output_id] = output_node
                state.recipe_edges.append(
                    RecipeEdge(
                        from_node_id=recipe_node_id,
                        to_node_id=output_id,
                        qty=scaled_qty,
                        type=RecipeEdgeType.PRODUCES,
                    )
                )

                if need and need.material_id and material_id == need.material_id:
                    qty = need.consumed_qty - need.produced_qty
                    state.material_edges.append(
                        MaterialEdge(from_node_id=output_id, to_node_id=need.id, qty=qty)
                    )
                    output_node.consumed_qty += qty
                    need.produced_qty += qty

        input_specs = (
            ("consumes", "I", MaterialNodeType.INPUT, RecipeEdgeType.CONSUMES),
            ("requires", "Rq", MaterialNodeType.REQUIRES, RecipeEdgeType.REQUIRES),
        )
        for slot_kind, node_prefix, node_type, edge_type in input_specs:
            for slot in recipe_materials[slot_kind]:
                for opt in slot["options"]:
                    material_id = first_matching_material_id(opt)
                    if material_id is None:
                        continue

                    scaled_qty = opt["quantity"] * exec_count
                    input_id = state.next_id(node_prefix)
                    state.material_nodes[input_id] = MaterialNode(
                        id=input_id,
                        material_id=material_id,
                        produced_qty=0.0,
                        consumed_qty=scaled_qty,
                        type=node_type,
                        rank=rank + 1,
                    )
                    state.recipe_edges.append(
                        RecipeEdge(
                            from_node_id=input_id,
                            to_node_id=recipe_node_id,
                            qty=scaled_qty,
                            type=edge_type,
                        )
                    )
                    new_inputs.append(input_id)

        return new_inputs

    def _apply_recipe(self, state, need_id, recipe_id, produces_option, request):
        need = state.material_nodes[need_id]
        per_exec = produces_option["quantity"]
        
        if request.domain_constraints.allow_partial_recipe_execution and per_exec > 0:
            exec_count = need.consumed_qty / per_exec
        else:
            exec_count = math.ceil(need.consumed_qty / per_exec) if per_exec > 0 else 1

        need_rank = need.rank
        rn_id = state.next_id("R")
        state.recipe_nodes[rn_id] = RecipeExecNode(id=rn_id, recipe_id=recipe_id, execution_count=exec_count, rank=need_rank)

        recipe_materials = self._get_materials_for_recipe(recipe_id, request.project_id)
        new_inputs = self._add_recipe_material_nodes(
            state=state,
            recipe_node_id=rn_id,
            recipe_materials=recipe_materials,
            exec_count=exec_count,
            rank=need_rank,
            output_type=MaterialNodeType.OUTPUT,
            target_need_id=need_id,
        )
        state.needs_queue.extendleft(reversed(new_inputs))

    def _initialize_material_target(self, request: SolverRequest) -> List["_State"]:
        """Initialize state for a material target. Returns a list of states, one per matching material."""
        # Find materials in the DB that match the target constraints
        matching_materials = self._find_materials_by_constraints(request.target.constraints, request.project_id)
        
        if not matching_materials:
            # No materials match - return empty list (will result in no solutions)
            return []
        
        # Create a state for each matching material
        states = []
        for i, material_id in enumerate(matching_materials):
            target_node = MaterialNode(
                id=f"T_{i:04d}",
                material_id=material_id,
                produced_qty=0.0,
                consumed_qty=request.target.quantity,
                type=MaterialNodeType.TARGET,
            )
            state = _State(
                material_nodes={target_node.id: target_node},
                recipe_nodes={},
                material_edges=[],
                recipe_edges=[],
                needs_queue=deque([target_node.id]),
                _counter=1,
            )
            states.append(state)
        
        return states

    def _initialize_recipe_target(self, request: SolverRequest, recipe_params: Dict) -> List["_State"]:
        """Initialize state for a recipe target. Returns a list of states, one per matching recipe."""
        # Find recipes matching the constraints using the resolution service
        matching_recipes = self._find_recipes_by_constraints(request.target.constraints, request.project_id)
        
        if not matching_recipes:
            # No recipes match - return empty list (will result in no solutions)
            return []
        
        # Create a state for each matching recipe
        states = []
        for i, recipe_id in enumerate(matching_recipes):
            # Use quantity directly as execution count (can be fractional if allowed)
            exec_count = request.target.quantity
            
            state = _State(
                material_nodes={},
                recipe_nodes={},
                material_edges=[],
                recipe_edges=[],
                needs_queue=deque(),
                _counter=1,
            )
            
            # Create recipe execution node
            rn_id = state.next_id("R")
            state.recipe_nodes[rn_id] = RecipeExecNode(id=rn_id, recipe_id=recipe_id, execution_count=exec_count, rank=0)
            
            recipe_materials = self._get_materials_for_recipe(recipe_id, request.project_id)
            new_inputs = self._add_recipe_material_nodes(
                state=state,
                recipe_node_id=rn_id,
                recipe_materials=recipe_materials,
                exec_count=exec_count,
                rank=0,
                output_type=MaterialNodeType.TARGET,
            )
            state.needs_queue = deque(new_inputs)
            states.append(state)
        
        return states

    def _find_surplus(self, state, need):
        need_amt = need.consumed_qty - need.produced_qty
        for nid, node in state.material_nodes.items():
            # Skip type 't' nodes (targets) - we want to keep them, not consume them
            if nid == need.id or node.type != MaterialNodeType.OUTPUT or node.type == MaterialNodeType.TARGET:
                continue
            if node.produced_qty - node.consumed_qty >= need_amt:
                # Compare material_ids instead of constraints
                if need.material_id and node.material_id and need.material_id == node.material_id:
                    return nid
        return None

    def _apply_surplus(self, state, surplus_id, need_id):
        sn = state.material_nodes[surplus_id]
        nn = state.material_nodes[need_id]
        qty = nn.consumed_qty - nn.produced_qty
        state.material_edges.append(MaterialEdge(from_node_id=surplus_id, to_node_id=need_id, qty=qty))
        nn.produced_qty += qty
        if nn.type != MaterialNodeType.REQUIRES:
            sn.consumed_qty += qty

    def _emit_plan(self, state, plans, seen_fps, score_rules, recipe_params, optimization_level: int = 0, domain_constraints=None, required_materials_ids=None, user_var_material_ids=None, required_recipes_by_rule=None):
        fp = self._fingerprint(state)
        if fp in seen_fps:
            return
        seen_fps.add(fp)

        if optimization_level == 1:
            state = self._optimize_level1(state)
        elif optimization_level >= 2:
            state = self._optimize_level2(state)

        # Tag state nodes before computing scores
        self._tag_state_nodes(state)

        # Check required materials and recipes before adding the plan
        if domain_constraints:
            if not self._check_required_materials(state, required_materials_ids):
                return
            if not self._check_required_recipes(state, required_recipes_by_rule, recipe_params):
                return

        all_nodes = list(state.material_nodes.values()) + list(state.recipe_nodes.values())
        score = self._compute_score(state, score_rules, recipe_params, user_var_material_ids)

        plans.append(SolvedPlan(
            plan_id="",
            graph_nodes=all_nodes,
            material_edges=list(state.material_edges),
            recipe_edges=list(state.recipe_edges),
            score=score,
        ))

    def _optimize_level1(self, state: "_State") -> "_State":
        """Optimization Level 1: replace each demand node's sources with a single
        surplus 'o' node where possible, then cascade execution-count reductions."""
        opt = _State(
            material_nodes={k: copy.copy(v) for k, v in state.material_nodes.items()},
            recipe_nodes={k: copy.copy(v) for k, v in state.recipe_nodes.items()},
            material_edges=[copy.copy(e) for e in state.material_edges],
            recipe_edges=[copy.copy(e) for e in state.recipe_edges],
            needs_queue=list(state.needs_queue),
            recipe_depth=state.recipe_depth,
            _counter=state._counter,
        )

        candidates = sorted(
            (n for n in opt.material_nodes.values()
             if n.type in (MaterialNodeType.INPUT, MaterialNodeType.TARGET)),
            key=lambda n: (n.rank, n.consumed_qty),
        )

        for snap in candidates:
            node_a_id = snap.id
            if node_a_id not in opt.material_nodes:
                continue
            node_a = opt.material_nodes[node_a_id]
            if node_a.consumed_qty <= 1e-9:
                continue

            initial_qty = node_a.consumed_qty
            node_a_material_id = node_a.material_id
            existing_sources = {me.from_node_id for me in opt.material_edges if me.to_node_id == node_a_id}

            best_c: Optional[Tuple[float, str]] = None
            for nid, node in opt.material_nodes.items():
                if node.type != MaterialNodeType.OUTPUT:
                    continue
                if nid in existing_sources:
                    continue
                # Compare material_ids instead of constraint signatures
                if node.material_id != node_a_material_id:
                    continue
                surplus = node.produced_qty - node.consumed_qty
                if surplus >= initial_qty - 1e-9:
                    if best_c is None or surplus < best_c[0]:
                        best_c = (surplus, nid)

            if best_c is None:
                continue

            node_c_id = best_c[1]
            node_c = opt.material_nodes[node_c_id]

            edges_to_remove = [me for me in opt.material_edges if me.to_node_id == node_a_id]
            opt.material_edges = [me for me in opt.material_edges if me.to_node_id != node_a_id]

            b_ids_to_cascade: List[str] = []
            for me in edges_to_remove:
                b_node = opt.material_nodes.get(me.from_node_id)
                node_a = opt.material_nodes.get(node_a_id)
                if node_a is not None:
                    node_a.produced_qty = max(0.0, node_a.produced_qty - me.qty)
                if b_node is not None:
                    b_node.consumed_qty = max(0.0, b_node.consumed_qty - me.qty)
                    b_ids_to_cascade.append(me.from_node_id)

            node_c.consumed_qty += initial_qty
            if node_a_id in opt.material_nodes:
                opt.material_nodes[node_a_id].produced_qty += initial_qty
            opt.material_edges.append(MaterialEdge(from_node_id=node_c_id, to_node_id=node_a_id, qty=initial_qty))

            for bid in b_ids_to_cascade:
                if bid in opt.material_nodes:
                    self._cascade_reduction(opt, bid)

        return opt

    def _optimize_level2(self, state: "_State") -> "_State":
        """Optimization Level 2: like Level 1 but multiple Node Cs can jointly
        satisfy Node A, and existing Node B edges are stripped smallest-first
        (partial reduction of the last edge allowed)."""
        opt = _State(
            material_nodes={k: copy.copy(v) for k, v in state.material_nodes.items()},
            recipe_nodes={k: copy.copy(v) for k, v in state.recipe_nodes.items()},
            material_edges=[copy.copy(e) for e in state.material_edges],
            recipe_edges=[copy.copy(e) for e in state.recipe_edges],
            needs_queue=list(state.needs_queue),
            recipe_depth=state.recipe_depth,
            _counter=state._counter,
        )

        candidates = sorted(
            (n for n in opt.material_nodes.values()
             if n.type in (MaterialNodeType.INPUT, MaterialNodeType.TARGET)),
            key=lambda n: (n.rank, n.consumed_qty),
        )

        for snap in candidates:
            node_a_id = snap.id
            if node_a_id not in opt.material_nodes:
                continue
            node_a = opt.material_nodes[node_a_id]
            if node_a.consumed_qty <= 1e-9:
                continue

            initial_qty = node_a.consumed_qty
            node_a_material_id = node_a.material_id
            existing_sources = {me.from_node_id for me in opt.material_edges if me.to_node_id == node_a_id}

            c1: List[Tuple[float, str]] = []
            c2: List[Tuple[float, str]] = []
            for nid, node in opt.material_nodes.items():
                if node.type != MaterialNodeType.OUTPUT:
                    continue
                if nid in existing_sources:
                    continue
                # Compare material_ids instead of constraint signatures
                if node.material_id != node_a_material_id:
                    continue
                surplus = node.produced_qty - node.consumed_qty
                if surplus >= initial_qty - 1e-9:
                    c1.append((surplus, nid))
                elif surplus > 1e-9:
                    c2.append((surplus, nid))

            if not c1 and not c2:
                continue

            selected: List[Tuple[str, float]] = []
            if c1:
                c1.sort(key=lambda x: x[0])
                selected.append((c1[0][1], initial_qty))
            else:
                c2.sort(key=lambda x: x[0], reverse=True)
                remaining_need = initial_qty
                for surplus, nid in c2:
                    if remaining_need <= 1e-9:
                        break
                    contribution = min(surplus, remaining_need)
                    selected.append((nid, contribution))
                    remaining_need -= contribution

            total_covered = sum(q for _, q in selected)
            selected_ids = {nid for nid, _ in selected}

            # Step A — add new source edges
            for node_c_id, contribution in selected:
                opt.material_nodes[node_c_id].consumed_qty += contribution
                opt.material_nodes[node_a_id].produced_qty += contribution
                opt.material_edges.append(MaterialEdge(from_node_id=node_c_id, to_node_id=node_a_id, qty=contribution))

            # Step B — remove/reduce existing B edges, smallest first
            b_edges = sorted(
                [me for me in opt.material_edges
                 if me.to_node_id == node_a_id and me.from_node_id not in selected_ids],
                key=lambda me: me.qty,
            )
            remaining_to_remove = total_covered
            b_ids_to_cascade: List[str] = []
            for me in b_edges:
                if remaining_to_remove <= 1e-9:
                    break
                b_node = opt.material_nodes.get(me.from_node_id)
                if b_node is None:
                    continue
                if remaining_to_remove >= me.qty - 1e-9:
                    reduce_by = me.qty
                    opt.material_edges = [x for x in opt.material_edges if x is not me]
                    b_node.consumed_qty = max(0.0, b_node.consumed_qty - reduce_by)
                    opt.material_nodes[node_a_id].produced_qty = max(0.0, opt.material_nodes[node_a_id].produced_qty - reduce_by)
                    remaining_to_remove = max(0.0, remaining_to_remove - reduce_by)
                else:
                    me.qty = max(0.0, me.qty - remaining_to_remove)
                    b_node.consumed_qty = max(0.0, b_node.consumed_qty - remaining_to_remove)
                    opt.material_nodes[node_a_id].produced_qty = max(0.0, opt.material_nodes[node_a_id].produced_qty - remaining_to_remove)
                    remaining_to_remove = 0.0
                b_ids_to_cascade.append(me.from_node_id)

            for bid in b_ids_to_cascade:
                if bid in opt.material_nodes:
                    self._cascade_reduction(opt, bid)

        return opt

    def _cascade_reduction(self, state: "_State", node_b_id: str) -> None:
        """Cascade Reduction: called after node_b.consumed_qty has been decreased.
        Recalculates the producing recipe's execution count and propagates upward."""
        if node_b_id not in state.material_nodes:
            return
        node_b = state.material_nodes[node_b_id]

        r_edge = next(
            (e for e in state.recipe_edges
             if e.to_node_id == node_b_id and e.type == RecipeEdgeType.PRODUCES),
            None,
        )

        if r_edge is None:
            if node_b.consumed_qty <= 1e-9:
                state.material_nodes.pop(node_b_id, None)
                state.material_edges = [e for e in state.material_edges if e.from_node_id != node_b_id]
            return

        r_id = r_edge.from_node_id
        r_node = state.recipe_nodes.get(r_id)
        if r_node is None:
            return

        if node_b.consumed_qty <= 1e-9:
            node_b.consumed_qty = 0.0
            state.material_nodes.pop(node_b_id, None)
            state.recipe_edges = [
                e for e in state.recipe_edges
                if not (e.from_node_id == r_id and e.to_node_id == node_b_id)
            ]
            state.material_edges = [e for e in state.material_edges if e.from_node_id != node_b_id]

        r_output_edges = [
            e for e in state.recipe_edges
            if e.from_node_id == r_id and e.type == RecipeEdgeType.PRODUCES
        ]
        old_exec = r_node.execution_count

        if not r_output_edges:
            new_exec = 0.0
        else:
            new_exec = 0.0
            for e in r_output_edges:
                out_node = state.material_nodes.get(e.to_node_id)
                if out_node is None or old_exec <= 0:
                    continue
                slot_qty = e.qty / old_exec
                if slot_qty > 0:
                    new_exec = max(new_exec, math.ceil(out_node.consumed_qty / slot_qty))

        if new_exec >= old_exec:
            return

        r_node.execution_count = new_exec

        for e in r_output_edges:
            out_node = state.material_nodes.get(e.to_node_id)
            if out_node is None or old_exec <= 0:
                continue
            slot_qty = e.qty / old_exec
            e.qty = slot_qty * new_exec
            out_node.produced_qty = slot_qty * new_exec

        r_input_edges = [
            e for e in state.recipe_edges
            if e.to_node_id == r_id and e.type in (RecipeEdgeType.CONSUMES, RecipeEdgeType.REQUIRES)
        ]
        upstream_to_cascade: List[str] = []
        for e in r_input_edges:
            i_node = state.material_nodes.get(e.from_node_id)
            if i_node is None or old_exec <= 0:
                continue
            slot_qty = e.qty / old_exec
            new_consumed = slot_qty * new_exec
            delta = e.qty - new_consumed
            if delta <= 1e-9:
                continue
            e.qty = new_consumed
            i_node.consumed_qty = max(0.0, i_node.consumed_qty - delta)
            remaining = delta
            for me in list(state.material_edges):
                if me.to_node_id != e.from_node_id or remaining <= 1e-9:
                    continue
                m_node = state.material_nodes.get(me.from_node_id)
                reduce_by = min(remaining, me.qty)
                me.qty = max(0.0, me.qty - reduce_by)
                if me.qty <= 1e-9:
                    state.material_edges = [x for x in state.material_edges if x is not me]
                if m_node is not None:
                    m_node.consumed_qty = max(0.0, m_node.consumed_qty - reduce_by)
                    if reduce_by > 1e-9:
                        upstream_to_cascade.append(m_node.id)
                remaining -= reduce_by

        if new_exec <= 0:
            orphan_input_ids = [
                e.from_node_id for e in r_input_edges
            ]
            orphan_output_ids = [
                e.to_node_id for e in r_output_edges
                if e.to_node_id in state.material_nodes
            ]
            state.recipe_edges = [
                e for e in state.recipe_edges
                if e.from_node_id != r_id and e.to_node_id != r_id
            ]
            state.recipe_nodes.pop(r_id, None)
            for nid in orphan_input_ids:
                state.material_nodes.pop(nid, None)
            for nid in orphan_output_ids:
                state.material_nodes.pop(nid, None)

        for mid in upstream_to_cascade:
            if mid in state.material_nodes:
                self._cascade_reduction(state, mid)

    def _fingerprint(self, state) -> str:
        parts = []
        for e in state.recipe_edges:
            if e.type == RecipeEdgeType.PRODUCES:
                rid = str(state.recipe_nodes[e.from_node_id].recipe_id)
                material_id = str(state.material_nodes[e.to_node_id].material_id) if state.material_nodes[e.to_node_id].material_id else "None"
            else:
                rid = str(state.recipe_nodes[e.to_node_id].recipe_id)
                material_id = str(state.material_nodes[e.from_node_id].material_id) if state.material_nodes[e.from_node_id].material_id else "None"
            parts.append(f"{rid}:{material_id}:{e.qty}:{e.type.value}")
        return "|".join(sorted(parts))

    def _find_producers(self, material_id: uuid.UUID, project_id: uuid.UUID, forbidden_recipes_ids: Set[uuid.UUID]) -> List[Tuple]:
        """Find recipes that can produce the given material."""
        # Get recipes that can produce this material
        recipes_data = self._get_recipes_for_material(material_id, project_id)
        
        producers = []
        for recipe_info in recipes_data["produces"]:
            recipe_id = uuid.UUID(recipe_info["recipe_id"])
            
            # Check if recipe is forbidden
            if recipe_id in forbidden_recipes_ids:
                continue
            
            # Add the recipe with its slot information
            for slot in recipe_info["slots"]:
                if slot["kind"] == "produces":
                    producers.append((recipe_id, {"quantity": slot["quantity"], "slot_id": slot["slot_id"]}))
                    break
        
        producers.sort(key=lambda x: str(x[0]))
        return producers

    def _constraints_match(self, target, candidate) -> bool:
        for tc in target:
            if not any(
                tc.domain == cc.domain and tc.key == cc.key and
                tc.operator == cc.operator and tc.value_string == cc.value_string and
                tc.value_number == cc.value_number and tc.value_boolean == cc.value_boolean
                for cc in candidate
            ):
                return False
        return True

    def _matches_rule(self, constraints, rules) -> bool:
        return any(self._constraints_match(constraints, r.constraints) for r in rules)

    def _check_required_materials(self, state, required_materials_ids) -> bool:
        """Check if the plan contains all required materials by ID."""
        if not required_materials_ids:
            return True
        
        # Get all material IDs from the plan
        plan_material_ids = {node.material_id for node in state.material_nodes.values() if node.material_id}
        
        # Check if all required material IDs are present in the plan
        return required_materials_ids.issubset(plan_material_ids)

    def _check_required_recipes(self, state, required_recipe_matching, recipe_params) -> bool:
        """Check if the plan contains all recipes matching the required constraints."""
        if not required_recipe_matching:
            return True
        
        # Get all recipe IDs used in the plan
        recipe_ids = set(node.recipe_id for node in state.recipe_nodes.values())
        
        # Check if each required rule has at least one matching recipe in the plan
        for rule_index, required_recipe_ids in required_recipe_matching.items():
            # Check if the plan contains at least one recipe from this required set
            if not recipe_ids.intersection(required_recipe_ids):
                return False
        
        return True

    def _compute_score(
        self, state: "_State", score_rules, recipe_params: Dict, user_var_material_ids: Dict[str, Set[uuid.UUID]]
    ) -> Dict[str, float]:
        """Compute all scores for a finished plan state."""
        scores: Dict[str, float] = {}

        # System: RecipeExecution
        scores["RecipeExecution"] = float(
            sum(n.execution_count for n in state.recipe_nodes.values())
        )

        # System: MaterialSplit
        n_mat_edges = len(state.material_edges)
        scores["MaterialSplit"] = (
            len(state.material_nodes) / n_mat_edges if n_mat_edges > 0 else 0.0
        )

        # System: SourceProduction
        # Sum consumed_qty of material root nodes
        source_production = 0.0
        for node in state.material_nodes.values():
            if "root" in node.tags:
                source_production += node.consumed_qty

        # For recipe root nodes, add consumed_qty of their output material nodes
        for rn in state.recipe_nodes.values():
            if "root" in rn.tags:
                # Find output edges from this recipe
                for re in state.recipe_edges:
                    if re.from_node_id == rn.id:
                        # Find the material node at the end of this edge
                        mat_node = state.material_nodes.get(re.to_node_id)
                        if mat_node:
                            source_production += mat_node.consumed_qty

        scores["SourceProduction"] = source_production

        # System: WasteProduced
        scores["WasteProduced"] = float(sum(
            max(0.0, n.produced_qty - n.consumed_qty)
            for n in state.material_nodes.values()
            if n.type == MaterialNodeType.OUTPUT
        ))

        if score_rules:
            var_values: Dict[str, float] = dict(scores)
            for var_def in score_rules.user_variables:
                value = self._compute_user_variable(state, var_def, recipe_params, user_var_material_ids)
                var_values[var_def.name] = value
                scores[var_def.name] = value
            for fdef in score_rules.score_formulas:
                scores[fdef.name] = self._evaluate_formula(fdef.formula, var_values)

        return scores

    def _compute_user_variable(
        self, state: "_State", var_def: "UserVariableDef", recipe_params: Dict, user_var_material_ids: Dict[str, Set[uuid.UUID]]
    ) -> float:
        total = 0.0
        if var_def.variable_type == "material":
            # Get pre-loaded material IDs for this variable
            var_material_ids = user_var_material_ids.get(var_def.name, set())
            
            for node in state.material_nodes.values():
                # Check if material_id matches the pre-loaded set
                if node.material_id and node.material_id in var_material_ids:
                    # Load material parameters from DB to extract parameter value
                    material_params = self._list_entity_params_cached(node.material_id)
                    param_value = self._extract_param_value_from_params(
                        material_params, var_def.parameter_domain, var_def.parameter_key
                    )
                    total += param_value * node.produced_qty
        else:  # "recipe"
            for rn in state.recipe_nodes.values():
                params = recipe_params.get(str(rn.recipe_id), [])
                if self._node_matches_var_constraints(params, var_def.constraints):
                    param_value = self._extract_param_value(
                        params, var_def.parameter_domain, var_def.parameter_key
                    )
                    total += param_value * rn.execution_count
        return total

    def _params_to_constraints(self, params: List) -> List[ConstraintSpec]:
        """Convert entity parameters to constraint specs."""
        constraints = []
        for param in params:
            constraint = ConstraintSpec(
                domain=param.domain,
                key=param.key,
                operator="=",
                value_string=param.value_string,
                value_number=param.value_number,
                value_boolean=param.value_boolean,
                is_wildcard=False,
            )
            constraints.append(constraint)
        return constraints

    @staticmethod
    def _node_matches_var_constraints(
        node_constraints: List[ConstraintSpec],
        var_constraints: List[List[ConstraintSpec]],
    ) -> bool:
        """Returns True if node matches any option group (OR of AND groups)."""
        if not var_constraints:
            return True
        for option in var_constraints:
            if all(
                any(
                    nc.domain == sc.domain and nc.key == sc.key
                    and nc.value_string == sc.value_string
                    and nc.value_number == sc.value_number
                    and nc.value_boolean == sc.value_boolean
                    for nc in node_constraints
                )
                for sc in option
            ):
                return True
        return False

    @staticmethod
    def _extract_param_value_from_params(params: List, domain: str, key: str) -> float:
        """Extract a numeric value from entity parameters for aggregation."""
        for param in params:
            if param.domain == domain and param.key == key:
                if param.value_number is not None:
                    return param.value_number
                if param.value_string is not None:
                    return 1.0  # count strings
        return 0.0

    @staticmethod
    def _extract_param_value(
        constraints: List[ConstraintSpec], domain: str, key: str
    ) -> float:
        """Extract a numeric value from a constraint list for aggregation."""
        for c in constraints:
            if c.domain == domain and c.key == key:
                if c.value_number is not None:
                    return c.value_number
                if c.value_string is not None:
                    return 1.0  # count strings
                if c.value_boolean is True:
                    return 1.0  # count trues
        return 0.0

    @staticmethod
    def _evaluate_formula(formula: str, variables: Dict[str, float]) -> float:
        try:
            result = eval(formula, {"__builtins__": {}}, dict(variables))
            return float(result)
        except ZeroDivisionError:
            return 0.0

    def _collect_entities(self, plans: List[SolvedPlan], project_id: uuid.UUID) -> Entities:
        """Collect all materials and recipes referenced in the plans."""
        material_ids: Set[uuid.UUID] = set()
        recipe_ids: Set[uuid.UUID] = set()

        for plan in plans:
            for node in plan.graph_nodes:
                if isinstance(node, RecipeExecNode):
                    recipe_ids.add(node.recipe_id)
                else:
                    if node.material_id:
                        material_ids.add(node.material_id)

        materials: Dict[uuid.UUID, EntityData] = {}
        recipes: Dict[uuid.UUID, EntityData] = {}

        if material_ids:
            for mid in material_ids:
                entity = self.entity_repo.get_by_id(mid)
                if entity and entity.project_id == project_id:
                    params = self._list_entity_params_cached(mid)
                    materials[mid] = EntityData(
                        id=entity.id, project_id=entity.project_id,
                        created_at=entity.created_at,
                        parameters=[self._to_spec(p) for p in params]
                    )

        if recipe_ids:
            for rid in recipe_ids:
                entity = self.entity_repo.get_by_id(rid)
                if entity and entity.project_id == project_id:
                    params = self._list_entity_params_cached(rid)
                    recipes[rid] = EntityData(
                        id=entity.id, project_id=entity.project_id,
                        created_at=entity.created_at,
                        parameters=[self._to_spec(p) for p in params]
                    )

        return Entities(materials=materials, recipes=recipes)

    def _load_recipe_params(
        self, recipe_ids: List[uuid.UUID]
    ) -> Dict[str, List[ConstraintSpec]]:
        """Load recipe entity parameters as ConstraintSpec lists, keyed by str(recipe_id)."""
        result: Dict[str, List[ConstraintSpec]] = {}
        for rid in recipe_ids:
            params = self._list_entity_params_cached(rid)
            result[str(rid)] = [
                ConstraintSpec(
                    domain=p.domain, key=p.key, operator="=",
                    value_string=p.value_string,
                    value_number=p.value_number,
                    value_boolean=p.value_boolean,
                )
                for p in params
            ]
        return result

    def _to_spec(self, c) -> ConstraintSpec:
        # Handle both ParameterConstraint (has operator) and Parameter (no operator)
        operator = getattr(c, "operator", "=")
        is_wildcard = getattr(c, "is_wildcard", False)
        return ConstraintSpec(
            domain=c.domain, key=c.key, operator=operator,
            value_string=c.value_string, value_number=c.value_number,
            value_boolean=c.value_boolean, is_wildcard=is_wildcard,
        )

    @staticmethod
    def _attr(obj: Any, name: str, default: Any = None) -> Any:
        """Read an attribute from either a domain object or a dict."""
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    @staticmethod
    def _value_to_label(value: Any) -> Optional[str]:
        if value is None:
            return None
        if value is False:
            return "False"
        return str(value)

    @staticmethod
    def _node_to_dict(node: Any) -> dict:
        if isinstance(node, RecipeExecNode):
            return {
                "id": node.id,
                "kind": "recipe_execution",
                "recipe_id": node.recipe_id,
                "execution_count": node.execution_count,
                "rank": node.rank,
                "tags": list(getattr(node, "tags", []) or []),
            }
        if isinstance(node, MaterialNode):
            return {
                "id": node.id,
                "kind": "material",
                "material_id": node.material_id,
                "produced_qty": node.produced_qty,
                "consumed_qty": node.consumed_qty,
                "type": node.type,
                "rank": node.rank,
                "tags": list(getattr(node, "tags", []) or []),
            }
        return dict(node)

    @staticmethod
    def _edge_to_dict(edge: Any) -> dict:
        if isinstance(edge, dict):
            return edge
        result = {
            "from_node_id": edge.from_node_id,
            "to_node_id": edge.to_node_id,
            "qty": edge.qty,
        }
        edge_type = getattr(edge, "type", None)
        if edge_type is not None:
            result["edge_type"] = getattr(edge_type, "value", edge_type)
        else:
            result["edge_type"] = "material"
        return result

    @staticmethod
    def _response_parts(data: Any) -> Tuple[bool, List[Any], Any]:
        """Accept either SolverResponse/domain objects or old dict-shaped payloads."""
        if isinstance(data, dict):
            return bool(data.get("success")), list(data.get("plans", [])), data.get("entities", {})
        return bool(getattr(data, "success", False)), list(getattr(data, "plans", []) or []), getattr(data, "entities", None)

    @staticmethod
    def _plan_graph(plan: Any) -> dict:
        if isinstance(plan, dict):
            graph = plan.get("graph")
            if graph:
                return graph
            return {
                "nodes": plan.get("graph_nodes", plan.get("nodes", [])),
                "edges": plan.get("material_edges", []) + plan.get("recipe_edges", []) + plan.get("edges", []),
            }
        return {
            "nodes": [OutputSolverService._node_to_dict(n) for n in getattr(plan, "graph_nodes", [])],
            "edges": [
                OutputSolverService._edge_to_dict(e)
                for e in chain(getattr(plan, "material_edges", []) or [], getattr(plan, "recipe_edges", []) or [])
            ],
        }

    @staticmethod
    def _entity_bucket(entities: Any, bucket: str) -> Dict[str, Any]:
        if not entities:
            return {}
        raw = entities.get(bucket, {}) if isinstance(entities, dict) else getattr(entities, bucket, {})
        return {str(k): v for k, v in (raw or {}).items()}

    @staticmethod
    def _entity_label(entities: Any, bucket: str, entity_id: Any, label_param: Optional[Tuple[str, str]]) -> Optional[str]:
        if not entity_id or not label_param:
            return None
        entity = OutputSolverService._entity_bucket(entities, bucket).get(str(entity_id))
        if not entity:
            return None
        params = entity.get("parameters", []) if isinstance(entity, dict) else getattr(entity, "parameters", [])
        domain, key = label_param
        for p in params or []:
            if OutputSolverService._attr(p, "domain") == domain and OutputSolverService._attr(p, "key") == key:
                return (
                    OutputSolverService._value_to_label(OutputSolverService._attr(p, "value_string"))
                    or OutputSolverService._value_to_label(OutputSolverService._attr(p, "value_number"))
                    or OutputSolverService._value_to_label(OutputSolverService._attr(p, "value_boolean"))
                )
        return None

    @staticmethod
    def _node_labels(
        nodes: Iterable[dict],
        entities: Any,
        material_label_param: Optional[Tuple[str, str]],
        recipe_label_param: Optional[Tuple[str, str]],
    ) -> Dict[str, str]:
        labels: Dict[str, str] = {}
        for n in nodes:
            node_id = n["id"]
            if n.get("kind") == "recipe_execution":
                recipe_id = n.get("recipe_id")
                labels[node_id] = (
                    OutputSolverService._entity_label(entities, "recipes", recipe_id, recipe_label_param)
                    or str(recipe_id or node_id)[:8]
                )
            else:
                material_id = n.get("material_id")
                labels[node_id] = (
                    OutputSolverService._entity_label(entities, "materials", material_id, material_label_param)
                    or str(material_id or node_id)[:8]
                )
        return labels

    @staticmethod
    def _fmt_qty(value: Any) -> str:
        if value is None:
            return "?"
        try:
            value = float(value)
            return str(int(value)) if value == int(value) else f"{value:.2f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def print_plan_graph(
        data: Any,
        material_label_param: Optional[Tuple[str, str]] = None,
        recipe_label_param: Optional[Tuple[str, str]] = None,
        simplify_level: int = 2,
    ) -> None:
        """Print a human-readable solver response plus Graphviz DOT.

        Works with both the current domain response returned by solve() and the older
        dict-shaped response used by early debugging scripts.
        """
        success, plans, entities = OutputSolverService._response_parts(data)
        print("\n" + "=" * 60)
        print(f"SOLVER OUTPUT  success={success}  plans={len(plans)}")

        for i, plan in enumerate(plans, 1):
            plan_id = plan.get("plan_id", "") if isinstance(plan, dict) else getattr(plan, "plan_id", "")
            score = plan.get("score", {}) if isinstance(plan, dict) else getattr(plan, "score", {})
            graph = OutputSolverService._plan_graph(plan)
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])
            node_id_to_label = OutputSolverService._node_labels(nodes, entities, material_label_param, recipe_label_param)

            print(f"\n--- Plan {i}: {plan_id} ---")
            print("Nodes:")
            for n in nodes:
                label = node_id_to_label.get(n["id"], n["id"])
                tags = n.get("tags", []) or []
                if n.get("kind") == "recipe_execution":
                    print(f"  {label}: recipe exec={OutputSolverService._fmt_qty(n.get('execution_count', 0))} tags={tags}")
                else:
                    node_type = getattr(n.get("type"), "value", n.get("type", "?"))
                    prod = OutputSolverService._fmt_qty(n.get("produced_qty", 0))
                    cons = OutputSolverService._fmt_qty(n.get("consumed_qty", 0))
                    print(f"  {label}: material type={node_type} prod={prod} cons={cons} tags={tags}")

            print("Edges:")
            for e in edges:
                from_label = node_id_to_label.get(e.get("from_node_id"), e.get("from_node_id"))
                to_label = node_id_to_label.get(e.get("to_node_id"), e.get("to_node_id"))
                print(
                    f"  {from_label} --> {to_label}: "
                    f"type={e.get('edge_type', '?')} qty={OutputSolverService._fmt_qty(e.get('qty', 0))}"
                )

            print("Scores:")
            for name, value in (score or {}).items():
                print(f"  {name}: {value}")

            simplified_graph = OutputSolverService.simplify_graph(graph, simplify_level)
            simplified_nodes = simplified_graph["nodes"]
            simplified_edges = simplified_graph["edges"]
            simplified_labels = OutputSolverService._node_labels(
                simplified_nodes, entities, material_label_param, recipe_label_param
            )

            print(f"\n// Graphviz for Plan {i} (simplify_level={simplify_level})")
            print("digraph {")
            print("  rankdir=LR;")

            for n in simplified_nodes:
                label = simplified_labels.get(n["id"], n["id"])
                if n.get("kind") == "recipe_execution":
                    exec_str = OutputSolverService._fmt_qty(n.get("execution_count", 1))
                    print(f'  "{n["id"]}" [label="{label}\\n({exec_str})", shape=circle, fillcolor="#444444", fontcolor="white", style="filled"];')
                else:
                    prod = OutputSolverService._fmt_qty(n.get("produced_qty", 0))
                    cons = OutputSolverService._fmt_qty(n.get("consumed_qty", 0))
                    tags = set(n.get("tags", []) or [])
                    if "excess" in tags:
                        color = "#ff6b6b"
                    elif "root" in tags:
                        color = "#4dabf7"
                    elif "leaf" in tags:
                        color = "#69db7c"
                    else:
                        color = "#ffd43b"
                    print(f'  "{n["id"]}" [label="{label}\\n{cons}/{prod}", shape=box, style="rounded,filled", fillcolor="{color}", fontcolor="black"];')

            qtys = [e.get("qty") for e in simplified_edges if e.get("qty") is not None]
            min_qty = min(qtys, default=1)
            max_qty = max(qtys, default=1)
            if max_qty == 0:
                max_qty = 1
            if min_qty == max_qty:
                min_qty = 0

            for e in simplified_edges:
                qty = e.get("qty", min_qty)
                qty = min_qty if qty is None else qty
                qty_str = OutputSolverService._fmt_qty(qty)
                width = 1 + (((qty - min_qty) / (max_qty - min_qty)) * 4.0) if max_qty != min_qty else 1
                width = min(max(width, 1), 5)
                print(f'  "{e.get("from_node_id")}" -> "{e.get("to_node_id")}" [label="{qty_str}", penwidth={width:.1f}];')

            print("}")

        print("=" * 60 + "\n")

    @staticmethod
    def _simplify_graph_lv0(graph: dict) -> dict:
        return graph

    @staticmethod
    def _simplify_graph_lv1(graph: dict) -> dict:
        """Collapse connected material nodes with the same material_id."""
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        material_nodes = [n for n in nodes if n.get("kind") != "recipe_execution" and n.get("material_id")]
        recipe_nodes = [n for n in nodes if n.get("kind") == "recipe_execution"]
        material_by_node = {n["id"]: str(n.get("material_id")) for n in material_nodes}
        material_node_lookup = {n["id"]: n for n in material_nodes}

        adjacency = {node_id: set() for node_id in material_by_node}
        for e in edges:
            from_id, to_id = e.get("from_node_id"), e.get("to_node_id")
            if from_id in material_by_node and to_id in material_by_node and material_by_node[from_id] == material_by_node[to_id]:
                adjacency[from_id].add(to_id)
                adjacency[to_id].add(from_id)

        clusters: List[List[str]] = []
        visited: Set[str] = set()
        for node_id in material_by_node:
            if node_id in visited:
                continue
            queue = deque([node_id])
            visited.add(node_id)
            cluster: List[str] = []
            while queue:
                current = queue.popleft()
                cluster.append(current)
                for nxt in adjacency[current]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
            clusters.append(cluster)

        node_to_collapsed: Dict[str, str] = {}
        collapsed_nodes: List[dict] = []
        for idx, cluster in enumerate(clusters):
            if len(cluster) == 1:
                node_to_collapsed[cluster[0]] = cluster[0]
                collapsed_nodes.append(material_node_lookup[cluster[0]])
                continue
            first = material_node_lookup[cluster[0]]
            material_id = material_by_node[cluster[0]]
            collapsed_id = f"CL{idx}_{material_id[:8]}"
            tags = set(chain.from_iterable(material_node_lookup[nid].get("tags", []) or [] for nid in cluster))
            tags.add("collapsed")
            for nid in cluster:
                node_to_collapsed[nid] = collapsed_id
            collapsed_nodes.append({
                "id": collapsed_id,
                "kind": "material",
                "type": first.get("type"),
                "material_id": first.get("material_id"),
                "produced_qty": 0,
                "consumed_qty": 0,
                "tags": list(tags),
            })

        new_edges = []
        for e in edges:
            new_from = node_to_collapsed.get(e.get("from_node_id"), e.get("from_node_id"))
            new_to = node_to_collapsed.get(e.get("to_node_id"), e.get("to_node_id"))
            if new_from == new_to:
                continue
            new_edges.append({**e, "from_node_id": new_from, "to_node_id": new_to})

        OutputSolverService._recalculate_collapsed_quantities(collapsed_nodes, new_edges)
        return {"nodes": recipe_nodes + collapsed_nodes, "edges": new_edges}

    @staticmethod
    def _simplify_graph_lv2(graph: dict) -> dict:
        """Collapse all material nodes by material_id."""
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        recipe_nodes = [n for n in nodes if n.get("kind") == "recipe_execution"]
        material_nodes = [n for n in nodes if n.get("kind") != "recipe_execution" and n.get("material_id")]
        material_by_node = {n["id"]: str(n.get("material_id")) for n in material_nodes}

        grouped: Dict[str, List[dict]] = {}
        for n in material_nodes:
            grouped.setdefault(str(n.get("material_id")), []).append(n)

        material_to_collapsed: Dict[str, str] = {}
        collapsed_nodes: List[dict] = []
        for material_id, group in grouped.items():
            first = group[0]
            collapsed_id = f"C_{material_id[:8]}"
            material_to_collapsed[material_id] = collapsed_id
            tags = set(chain.from_iterable(n.get("tags", []) or [] for n in group))
            tags.add("collapsed")
            collapsed_nodes.append({
                "id": collapsed_id,
                "kind": "material",
                "type": first.get("type"),
                "material_id": first.get("material_id"),
                "produced_qty": 0,
                "consumed_qty": 0,
                "tags": list(tags),
            })

        new_edges = []
        for e in edges:
            from_id, to_id = e.get("from_node_id"), e.get("to_node_id")
            from_is_material = from_id in material_by_node
            to_is_material = to_id in material_by_node
            if from_is_material and to_is_material:
                continue
            new_edges.append({
                **e,
                "from_node_id": material_to_collapsed[material_by_node[from_id]] if from_is_material else from_id,
                "to_node_id": material_to_collapsed[material_by_node[to_id]] if to_is_material else to_id,
            })

        OutputSolverService._recalculate_collapsed_quantities(collapsed_nodes, new_edges)
        return {"nodes": recipe_nodes + collapsed_nodes, "edges": new_edges}

    @staticmethod
    def _recalculate_collapsed_quantities(nodes: List[dict], edges: List[dict]) -> None:
        for node in nodes:
            node_id = node["id"]
            node["produced_qty"] = sum((e.get("qty") or 0) for e in edges if e.get("to_node_id") == node_id)
            node["consumed_qty"] = sum((e.get("qty") or 0) for e in edges if e.get("from_node_id") == node_id)

    @staticmethod
    def simplify_graph(graph: dict, simplify_level: int = 2) -> dict:
        """Simplify graph for debugging/Graphviz output.

        Level 0: no simplification.
        Level 1: collapse connected material-node clusters with the same material_id.
        Level 2: collapse all material nodes by material_id.
        """
        if simplify_level == 0:
            return OutputSolverService._simplify_graph_lv0(graph)
        if simplify_level == 1:
            return OutputSolverService._simplify_graph_lv1(graph)
        if simplify_level == 2:
            return OutputSolverService._simplify_graph_lv2(graph)
        return graph

