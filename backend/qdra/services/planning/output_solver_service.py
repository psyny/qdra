import copy
import math
import re
import uuid
from typing import List, Dict, Optional, Set, Tuple, FrozenSet
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from models.slot import SlotKind
from models.material import Material
from models.recipe import Recipe
from repositories.recipe_repository import RecipeRepository
from repositories.material_repository import MaterialRepository
from repositories.slot_repository import SlotRepository
from repositories.option_repository import OptionRepository
from repositories.parameter_constraint_repository import ParameterConstraintRepository
from repositories.project_repository import ProjectRepository

from domain.planning.output_solver_domain import (
    MaterialNode, RecipeExecNode, MaterialEdge, RecipeEdge,
    MaterialNodeType, RecipeEdgeType, ConstraintSpec, ConstraintRule,
    SolvedPlan, SolverRequest, SolverResponse,
    UserVariableDef, ScoreFormulaDef, ScoreRules, SYSTEM_VARIABLE_NAMES,
    Entities, EntityData,
)


@dataclass
class _State:
    material_nodes: Dict[str, MaterialNode]
    recipe_nodes: Dict[str, RecipeExecNode]
    material_edges: List[MaterialEdge]
    recipe_edges: List[RecipeEdge]
    needs_queue: List[str]
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
            needs_queue=list(self.needs_queue),
            recipe_depth=self.recipe_depth,
            _counter=self._counter,
        )


def _sig(constraints: List[ConstraintSpec]) -> str:
    parts = []
    for c in constraints:
        p = f"{c.domain}.{c.key}"
        if c.value_string is not None:
            p += f"={c.value_string}"
        elif c.value_number is not None:
            p += f"={c.value_number}"
        elif c.value_boolean is not None:
            p += f"={c.value_boolean}"
        parts.append(p)
    return ",".join(sorted(parts))


_SLOT_ORDER = {SlotKind.PRODUCES: 0, SlotKind.CONSUMES: 1, SlotKind.REQUIRES: 2}


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
        self.recipe_repo = RecipeRepository(db)
        self.material_repo = MaterialRepository(db)
        self.slot_repo = SlotRepository(db)
        self.option_repo = OptionRepository(db)
        self.constraint_repo = ParameterConstraintRepository(db)
        self.project_repo = ProjectRepository(db)

    def solve(self, request: SolverRequest) -> SolverResponse:
        if not self.project_repo.get_by_id(request.project_id):
            return SolverResponse(success=False)

        if request.score_rules and request.score_rules.score_formulas:
            system_names = set(SYSTEM_VARIABLE_NAMES)
            user_names = {v.name for v in request.score_rules.user_variables}
            all_names = system_names | user_names
            for fdef in request.score_rules.score_formulas:
                validate_formula(fdef.formula, all_names)

        recipes = self.recipe_repo.list_by_project(request.project_id)
        recipe_structures = {r.id: self._load_recipe_structure(r.id) for r in recipes}

        recipe_params: Dict[str, List[ConstraintSpec]] = {}
        if request.score_rules and any(
            v.variable_type == "recipe" for v in request.score_rules.user_variables
        ):
            recipe_params = self._load_recipe_params([r.id for r in recipes])

        target_node = MaterialNode(
            id="T_0001",
            material_constraints=request.target.constraints,
            produced_qty=0.0,
            consumed_qty=request.target.quantity,
            type=MaterialNodeType.TARGET,
        )
        initial = _State(
            material_nodes={"T_0001": target_node},
            recipe_nodes={},
            material_edges=[],
            recipe_edges=[],
            needs_queue=["T_0001"],
            _counter=1,
        )

        plans: List[SolvedPlan] = []
        seen_fps: Set[str] = set()
        self._explore(initial, recipe_structures, request, plans, seen_fps, frozenset(), recipe_params)

        for i, plan in enumerate(plans):
            plan.plan_id = f"plan_{i:03d}"
            self._tag_nodes(plan)

        entities = self._collect_entities(plans, request.project_id)
        return SolverResponse(success=True, plans=plans, entities=entities)

    def _tag_state_nodes(self, state: "_State") -> None:
        """Tag material and recipe nodes in the state based on graph topology."""
        # Build adjacency maps
        outgoing: Dict[str, List[str]] = {}
        incoming: Dict[str, List[str]] = {}

        for e in state.material_edges:
            if e.from_node_id not in outgoing:
                outgoing[e.from_node_id] = []
            outgoing[e.from_node_id].append(e.to_node_id)

            if e.to_node_id not in incoming:
                incoming[e.to_node_id] = []
            incoming[e.to_node_id].append(e.from_node_id)

        for e in state.recipe_edges:
            if e.from_node_id not in outgoing:
                outgoing[e.from_node_id] = []
            outgoing[e.from_node_id].append(e.to_node_id)

            if e.to_node_id not in incoming:
                incoming[e.to_node_id] = []
            incoming[e.to_node_id].append(e.from_node_id)

        # Tag material nodes
        for node in state.material_nodes.values():
            tags: Set[str] = set()

            if node.produced_qty > node.consumed_qty:
                tags.add("excess")

            if node.id not in outgoing or not outgoing[node.id]:
                tags.add("leaf")

            if node.id not in incoming or not incoming[node.id]:
                tags.add("root")

            node.tags = list(tags)

        # Tag recipe nodes as root if they have no incoming edges
        for rn in state.recipe_nodes.values():
            tags: Set[str] = set()
            if rn.id not in incoming or not incoming[rn.id]:
                tags.add("root")

            rn.tags = list(tags)

    def _tag_nodes(self, plan: SolvedPlan) -> None:
        """Tag material nodes based on graph topology and quantities."""
        # Build adjacency maps
        outgoing: Dict[str, List[str]] = {}
        incoming: Dict[str, List[str]] = {}

        for e in plan.material_edges:
            if e.from_node_id not in outgoing:
                outgoing[e.from_node_id] = []
            outgoing[e.from_node_id].append(e.to_node_id)

            if e.to_node_id not in incoming:
                incoming[e.to_node_id] = []
            incoming[e.to_node_id].append(e.from_node_id)

        for e in plan.recipe_edges:
            if e.from_node_id not in outgoing:
                outgoing[e.from_node_id] = []
            outgoing[e.from_node_id].append(e.to_node_id)

            if e.to_node_id not in incoming:
                incoming[e.to_node_id] = []
            incoming[e.to_node_id].append(e.from_node_id)

        # Tag material nodes
        for node in plan.graph_nodes:
            if not isinstance(node, MaterialNode):
                continue

            tags: Set[str] = set()

            if node.produced_qty > node.consumed_qty:
                tags.add("excess")

            if node.id not in outgoing or not outgoing[node.id]:
                tags.add("leaf")

            if node.id not in incoming or not incoming[node.id]:
                tags.add("root")

            node.tags = list(tags)

        # Tag recipe nodes as root if they have no incoming edges
        for node in plan.graph_nodes:
            if not isinstance(node, RecipeExecNode):
                continue

            tags: Set[str] = set()
            if node.id not in incoming or not incoming[node.id]:
                tags.add("root")

            node.tags = list(tags)

    def _explore(self, state, recipe_structures, request, plans, seen_fps, ancestor_sigs, recipe_params):
        if len(plans) >= request.search_parameters.max_solutions_returned:
            return

        current_id = None
        while state.needs_queue:
            nid = state.needs_queue.pop(0)
            node = state.material_nodes.get(nid)
            if node is not None and node.produced_qty < node.consumed_qty:
                current_id = nid
                break

        if current_id is None:
            self._emit_plan(state, plans, seen_fps, request.score_rules, recipe_params)
            return

        current = state.material_nodes[current_id]
        sig = _sig(current.material_constraints)

        if not request.search_parameters.allow_loops and sig in ancestor_sigs:
            return
        if state.recipe_depth >= request.domain_constraints.max_recipe_depth:
            return
        if state.recipe_depth >= request.search_parameters.max_recursion_depth:
            return

        surplus_id = self._find_surplus(state, current)
        if surplus_id is not None:
            branch = state.clone()
            self._apply_surplus(branch, surplus_id, current_id)
            self._explore(branch, recipe_structures, request, plans, seen_fps, ancestor_sigs, recipe_params)
            return

        if self._matches_rule(current.material_constraints, request.domain_constraints.do_not_expand_materials_matching):
            self._explore(state, recipe_structures, request, plans, seen_fps, ancestor_sigs, recipe_params)
            return

        if self._matches_rule(current.material_constraints, request.domain_constraints.forbidden_materials_matching):
            return

        producers = self._find_producers(
            current.material_constraints, recipe_structures,
            request.domain_constraints.forbidden_recipe_ids,
        )

        if not producers:
            self._explore(state, recipe_structures, request, plans, seen_fps, ancestor_sigs, recipe_params)
            return

        producers = producers[: request.search_parameters.max_branch_width]
        new_sigs = ancestor_sigs | {sig}

        for recipe_id, produces_option in producers:
            if len(plans) >= request.search_parameters.max_solutions_returned:
                return
            branch = state.clone()
            self._apply_recipe(branch, current_id, recipe_id, produces_option, recipe_structures)
            branch.recipe_depth += 1
            self._explore(branch, recipe_structures, request, plans, seen_fps, new_sigs, recipe_params)

    def _apply_recipe(self, state, need_id, recipe_id, produces_option, recipe_structures):
        need = state.material_nodes[need_id]
        per_exec = produces_option["quantity"]
        exec_count = math.ceil(need.consumed_qty / per_exec) if per_exec > 0 else 1

        rn_id = state.next_id("R")
        state.recipe_nodes[rn_id] = RecipeExecNode(id=rn_id, recipe_id=recipe_id, execution_count=exec_count)

        slots = sorted(recipe_structures[recipe_id]["slots"], key=lambda s: _SLOT_ORDER.get(s["kind"], 9))
        new_inputs: List[str] = []

        for slot in slots:
            if slot["kind"] == SlotKind.PRODUCES:
                for opt in slot["options"]:
                    oid = state.next_id("O")
                    onode = MaterialNode(
                        id=oid, material_constraints=opt["constraints"],
                        produced_qty=opt["quantity"] * exec_count,
                        consumed_qty=0.0, type=MaterialNodeType.OUTPUT,
                    )
                    state.material_nodes[oid] = onode
                    state.recipe_edges.append(RecipeEdge(from_node_id=rn_id, to_node_id=oid, qty=opt["quantity"] * exec_count, type=RecipeEdgeType.PRODUCES))
                    if self._constraints_match(need.material_constraints, opt["constraints"]):
                        qty = need.consumed_qty - need.produced_qty
                        state.material_edges.append(MaterialEdge(from_node_id=oid, to_node_id=need_id, qty=qty))
                        onode.consumed_qty += qty
                        state.material_nodes[need_id].produced_qty += qty

            elif slot["kind"] == SlotKind.CONSUMES:
                for opt in slot["options"]:
                    scaled = opt["quantity"] * exec_count
                    iid = state.next_id("I")
                    state.material_nodes[iid] = MaterialNode(id=iid, material_constraints=opt["constraints"], produced_qty=0.0, consumed_qty=scaled, type=MaterialNodeType.INPUT)
                    state.recipe_edges.append(RecipeEdge(from_node_id=iid, to_node_id=rn_id, qty=scaled, type=RecipeEdgeType.CONSUMES))
                    new_inputs.append(iid)

            elif slot["kind"] == SlotKind.REQUIRES:
                for opt in slot["options"]:
                    scaled = opt["quantity"] * exec_count
                    qid = state.next_id("Rq")
                    state.material_nodes[qid] = MaterialNode(id=qid, material_constraints=opt["constraints"], produced_qty=0.0, consumed_qty=scaled, type=MaterialNodeType.REQUIRES)
                    state.recipe_edges.append(RecipeEdge(from_node_id=qid, to_node_id=rn_id, qty=scaled, type=RecipeEdgeType.REQUIRES))
                    new_inputs.append(qid)

        state.needs_queue = new_inputs + state.needs_queue

    def _find_surplus(self, state, need):
        need_amt = need.consumed_qty - need.produced_qty
        for nid, node in state.material_nodes.items():
            if nid == need.id or node.type != MaterialNodeType.OUTPUT:
                continue
            if node.produced_qty - node.consumed_qty >= need_amt:
                if self._constraints_match(need.material_constraints, node.material_constraints):
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

    def _emit_plan(self, state, plans, seen_fps, score_rules, recipe_params):
        fp = self._fingerprint(state)
        if fp in seen_fps:
            return
        seen_fps.add(fp)

        # Tag state nodes before computing scores
        self._tag_state_nodes(state)

        all_nodes = list(state.material_nodes.values()) + list(state.recipe_nodes.values())
        score = self._compute_score(state, score_rules, recipe_params)

        plans.append(SolvedPlan(
            plan_id="",
            graph_nodes=all_nodes,
            material_edges=list(state.material_edges),
            recipe_edges=list(state.recipe_edges),
            score=score,
        ))

    def _fingerprint(self, state) -> str:
        parts = []
        for e in state.recipe_edges:
            if e.type == RecipeEdgeType.PRODUCES:
                rid = str(state.recipe_nodes[e.from_node_id].recipe_id)
                mkey = _sig(state.material_nodes[e.to_node_id].material_constraints)
            else:
                rid = str(state.recipe_nodes[e.to_node_id].recipe_id)
                mkey = _sig(state.material_nodes[e.from_node_id].material_constraints)
            parts.append(f"{rid}:{mkey}:{e.qty}:{e.type.value}")
        return "|".join(sorted(parts))

    def _find_producers(self, constraints, recipe_structures, forbidden_ids) -> List[Tuple]:
        producers = []
        for rid, structure in recipe_structures.items():
            if rid in forbidden_ids:
                continue
            for slot in structure["slots"]:
                if slot["kind"] == SlotKind.PRODUCES:
                    for opt in slot["options"]:
                        if self._constraints_match(constraints, opt["constraints"]):
                            producers.append((rid, opt))
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

    def _compute_score(
        self, state: "_State", score_rules, recipe_params: Dict
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

        if score_rules:
            var_values: Dict[str, float] = dict(scores)
            for var_def in score_rules.user_variables:
                value = self._compute_user_variable(state, var_def, recipe_params)
                var_values[var_def.name] = value
                scores[var_def.name] = value
            for fdef in score_rules.score_formulas:
                scores[fdef.name] = self._evaluate_formula(fdef.formula, var_values)

        return scores

    def _compute_user_variable(
        self, state: "_State", var_def: "UserVariableDef", recipe_params: Dict
    ) -> float:
        total = 0.0
        if var_def.variable_type == "material":
            for node in state.material_nodes.values():
                if self._node_matches_var_constraints(node.material_constraints, var_def.constraints):
                    param_value = self._extract_param_value(
                        node.material_constraints, var_def.parameter_domain, var_def.parameter_key
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
                    for c in node.material_constraints:
                        if c.domain == "identity" and c.key == "material_id" and c.value_string:
                            try:
                                material_ids.add(uuid.UUID(c.value_string))
                            except ValueError:
                                pass

        materials: Dict[uuid.UUID, EntityData] = {}
        recipes: Dict[uuid.UUID, EntityData] = {}

        if material_ids:
            db_materials = self.db.query(Material).filter(
                Material.id.in_(material_ids), Material.project_id == project_id
            ).all()
            from repositories.parameter_repository import ParameterRepository
            param_repo = ParameterRepository(self.db)
            for m in db_materials:
                params = param_repo.list_by_material(m.id)
                materials[m.id] = EntityData(
                    id=m.id, project_id=m.project_id, created_at=m.created_at,
                    parameters=[self._to_spec(p) for p in params]
                )

        if recipe_ids:
            db_recipes = self.db.query(Recipe).filter(
                Recipe.id.in_(recipe_ids), Recipe.project_id == project_id
            ).all()
            from repositories.recipe_parameter_repository import RecipeParameterRepository
            recipe_param_repo = RecipeParameterRepository(self.db)
            for r in db_recipes:
                params = recipe_param_repo.list_by_recipe(r.id)
                recipes[r.id] = EntityData(
                    id=r.id, project_id=r.project_id, created_at=r.created_at,
                    parameters=[self._to_spec(p) for p in params]
                )

        return Entities(materials=materials, recipes=recipes)

    def _load_recipe_params(
        self, recipe_ids: List[uuid.UUID]
    ) -> Dict[str, List[ConstraintSpec]]:
        """Load recipe parameters as ConstraintSpec lists, keyed by str(recipe_id)."""
        from repositories.recipe_parameter_repository import RecipeParameterRepository
        param_repo = RecipeParameterRepository(self.db)
        result: Dict[str, List[ConstraintSpec]] = {}
        for rid in recipe_ids:
            params = param_repo.list_by_recipe(rid)
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

    def _load_recipe_structure(self, recipe_id: uuid.UUID) -> Dict:
        slots = self.slot_repo.list_by_recipe(recipe_id)
        structure = {"recipe_id": recipe_id, "slots": []}
        for slot in slots:
            options = self.option_repo.list_by_slot(slot.id)
            slot_data = {"id": slot.id, "kind": slot.kind, "options": []}
            for opt in options:
                constraints = self.constraint_repo.list_by_option(opt.id)
                slot_data["options"].append({
                    "id": opt.id,
                    "quantity": opt.quantity,
                    "constraints": [self._to_spec(c) for c in constraints],
                })
            structure["slots"].append(slot_data)
        return structure

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
    def print_plan_graph(
        data: dict,
        material_label_param: Optional[Tuple[str, str]] = None,
        recipe_label_param: Optional[Tuple[str, str]] = None,
    ) -> None:
        print("\n" + "=" * 60)
        print(f"SOLVER OUTPUT  success={data.get('success')}  plans={len(data.get('plans', []))}")
        for i, plan in enumerate(data.get("plans", []), 1):
            print(f"\n--- Plan {i}: {plan.get('plan_id')} ---")
            graph = plan.get("graph", {})
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])

            # Build label mappings using entities data
            entities = data.get("entities", {})
            node_id_to_label: Dict[str, str] = {}
            for n in nodes:
                nid = n["id"]
                if n.get("kind") == "recipe_execution":
                    label = str(n.get("recipe_id", nid))[:8]
                    if recipe_label_param:
                        domain, key = recipe_label_param
                        recipe_id = n.get("recipe_id")
                        if recipe_id and "recipes" in entities:
                            recipe_data = entities["recipes"].get(str(recipe_id))
                            if recipe_data and "parameters" in recipe_data:
                                for p in recipe_data["parameters"]:
                                    if p.get("domain") == domain and p.get("key") == key:
                                        val = p.get("value_string") or p.get("value_number") or p.get("value_boolean")
                                        if val is not None:
                                            label = str(val)
                                            break
                    node_id_to_label[nid] = label
                else:
                    label = nid
                    if material_label_param:
                        domain, key = material_label_param
                        for c in n.get("material_constraints", []):
                            if c.get("domain") == "identity" and c.get("key") == "material_id" and c.get("value_string"):
                                material_id = c.get("value_string")
                                if material_id and "materials" in entities:
                                    mat_data = entities["materials"].get(material_id)
                                    if mat_data and "parameters" in mat_data:
                                        for p in mat_data["parameters"]:
                                            if p.get("domain") == domain and p.get("key") == key:
                                                val = p.get("value_string") or p.get("value_number") or p.get("value_boolean")
                                                if val is not None:
                                                    label = str(val)
                                                    break
                    node_id_to_label[nid] = label

            # Print nodes
            print("Nodes:")
            for n in nodes:
                label = node_id_to_label[n["id"]]
                if n.get("kind") == "recipe_execution":
                    tags = n.get("tags", [])
                    print(f"  {label}: recipe exec={n.get('execution_count')} tags={tags}")
                else:
                    node_type = n.get("type", "?")
                    prod = n.get("produced_qty", 0)
                    cons = n.get("consumed_qty", 0)
                    tags = n.get("tags", [])
                    print(f"  {label}: material type={node_type} prod={prod} cons={cons} tags={tags}")

            # Print edges
            print("Edges:")
            for e in edges:
                from_label = node_id_to_label.get(e.get("from_node_id"), e.get("from_node_id"))
                to_label = node_id_to_label.get(e.get("to_node_id"), e.get("to_node_id"))
                edge_type = e.get("edge_type", "?")
                qty = e.get("qty", 0)
                print(f"  {from_label} --> {to_label}: type={edge_type} qty={qty}")

            # Print scores
            print("Scores:")
            score = plan.get("score", {})
            for name, value in score.items():
                print(f"  {name}: {value}")

            # Simplify graph for graphviz output
            simplified_graph = OutputSolverService.simplify_graph(graph)
            simplified_nodes = simplified_graph["nodes"]
            simplified_edges = simplified_graph["edges"]

            # Rebuild label mapping for simplified nodes
            simplified_node_id_to_label = {}
            for n in simplified_nodes:
                nid = n["id"]
                if n.get("kind") == "recipe_execution":
                    label = str(n.get("recipe_id", nid))[:8]
                    if recipe_label_param:
                        domain, key = recipe_label_param
                        recipe_id = n.get("recipe_id")
                        if recipe_id and "recipes" in entities:
                            recipe_data = entities["recipes"].get(str(recipe_id))
                            if recipe_data and "parameters" in recipe_data:
                                for p in recipe_data["parameters"]:
                                    if p.get("domain") == domain and p.get("key") == key:
                                        val = p.get("value_string") or p.get("value_number") or p.get("value_boolean")
                                        if val is not None:
                                            label = str(val)
                                            break
                    simplified_node_id_to_label[nid] = label
                else:
                    # For collapsed material nodes, use entities to get label
                    label = nid
                    if material_label_param:
                        domain, key = material_label_param
                        for c in n.get("material_constraints", []):
                            if c.get("domain") == "identity" and c.get("key") == "material_id" and c.get("value_string"):
                                material_id = c.get("value_string")
                                if material_id and "materials" in entities:
                                    mat_data = entities["materials"].get(material_id)
                                    if mat_data and "parameters" in mat_data:
                                        for p in mat_data["parameters"]:
                                            if p.get("domain") == domain and p.get("key") == key:
                                                val = p.get("value_string") or p.get("value_number") or p.get("value_boolean")
                                                if val is not None:
                                                    label = str(val)
                                                    break
                    simplified_node_id_to_label[nid] = label

            # Print graphviz dot code
            print(f"\n// Graphviz for Plan {i} (simplified)")
            print("digraph {")
            print("  rankdir=LR;")

            # Calculate max edge qty for width scaling
            max_qty = max((e.get("qty", 0) for e in simplified_edges), default=1)
            if max_qty == 0:
                max_qty = 1

            # Print graphviz nodes
            for n in simplified_nodes:
                label = simplified_node_id_to_label[n["id"]]
                if n.get("kind") == "recipe_execution":
                    exec_count = n.get("execution_count", 1)
                    print(f'  "{n["id"]}" [label="{label}\\n({exec_count})", shape=circle, fillcolor="#444444", fontcolor="white", style="filled"];')
                else:
                    prod = n.get("produced_qty", 0)
                    cons_qty = n.get("consumed_qty", 0)
                    tags = n.get("tags", [])

                    # Determine color based on tags
                    if "excess" in tags:
                        color = "#ff6b6b"  # red
                    elif "root" in tags:
                        color = "#4dabf7"  # blue
                    elif "leaf" in tags:
                        color = "#69db7c"  # green
                    else:
                        color = "#ffd43b"  # yellow

                    print(f'  "{n["id"]}" [label="{label}\\n{cons_qty}/{prod}", shape=box, style="rounded,filled", fillcolor="{color}", fontcolor="black"];')

            # Print graphviz edges
            for e in simplified_edges:
                qty = e.get("qty", 0)
                width = 1 + (qty / max_qty) * 3  # scale 1-4
                width = min(max(width, 1), 4)
                from_label = simplified_node_id_to_label.get(e.get("from_node_id"), e.get("from_node_id"))
                to_label = simplified_node_id_to_label.get(e.get("to_node_id"), e.get("to_node_id"))
                print(f'  "{e.get("from_node_id")}" -> "{e.get("to_node_id")}" [label="{qty}", penwidth={width:.1f}];')

            print("}")

        print("=" * 60 + "\n")

    @staticmethod
    def simplify_graph(graph: dict) -> dict:
        """Simplify graph by collapsing material nodes of the same type (material_id)."""
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # Group material nodes by material_id
        material_id_to_nodes = {}
        recipe_nodes = []
        node_id_to_material_id = {}

        for node in nodes:
            if node.get("kind") == "recipe_execution":
                recipe_nodes.append(node)
            else:
                # Extract material_id from constraints
                material_id = None
                for c in node.get("material_constraints", []):
                    if c.get("domain") == "identity" and c.get("key") == "material_id":
                        material_id = c.get("value_string")
                        break
                if material_id:
                    if material_id not in material_id_to_nodes:
                        material_id_to_nodes[material_id] = []
                    material_id_to_nodes[material_id].append(node)
                    node_id_to_material_id[node["id"]] = material_id

        # Create collapsed material nodes
        collapsed_nodes = []
        material_id_to_collapsed_id = {}

        for material_id, mat_nodes in material_id_to_nodes.items():
            # Merge tags from all nodes, add "collapsed"
            merged_tags = set()
            for n in mat_nodes:
                merged_tags.update(n.get("tags", []))
            merged_tags.add("collapsed")

            # Generate collapsed node id
            collapsed_id = f"C_{material_id[:8]}"
            material_id_to_collapsed_id[material_id] = collapsed_id

            # Create collapsed node with first node's constraints
            first_node = mat_nodes[0]
            collapsed_node = {
                "id": collapsed_id,
                "kind": "material",
                "type": first_node.get("type"),
                "material_constraints": first_node.get("material_constraints"),
                "produced_qty": 0,  # Will recalculate
                "consumed_qty": 0,  # Will recalculate
                "tags": list(merged_tags),
            }
            collapsed_nodes.append(collapsed_node)

        # Build new edges (discard material-to-material edges)
        new_edges = []

        for edge in edges:
            from_id = edge.get("from_node_id")
            to_id = edge.get("to_node_id")

            # Check if from/to is a material node
            from_is_material = from_id in node_id_to_material_id
            to_is_material = to_id in node_id_to_material_id

            # Discard material-to-material edges
            if from_is_material and to_is_material:
                continue

            # Map material node IDs to collapsed IDs
            new_from_id = from_id
            new_to_id = to_id

            if from_is_material:
                material_id = node_id_to_material_id[from_id]
                new_from_id = material_id_to_collapsed_id[material_id]

            if to_is_material:
                material_id = node_id_to_material_id[to_id]
                new_to_id = material_id_to_collapsed_id[material_id]

            new_edges.append({
                "from_node_id": new_from_id,
                "to_node_id": new_to_id,
                "qty": edge.get("qty"),
                "edge_type": edge.get("edge_type"),
            })

        # Recalculate produced/consumed for collapsed nodes
        for collapsed_node in collapsed_nodes:
            collapsed_id = collapsed_node["id"]
            produced = 0
            consumed = 0

            for edge in new_edges:
                if edge["to_node_id"] == collapsed_id:
                    produced += edge.get("qty", 0)
                if edge["from_node_id"] == collapsed_id:
                    consumed += edge.get("qty", 0)

            collapsed_node["produced_qty"] = produced
            collapsed_node["consumed_qty"] = consumed

        # Combine recipe nodes and collapsed material nodes
        simplified_nodes = recipe_nodes + collapsed_nodes

        return {
            "nodes": simplified_nodes,
            "edges": new_edges,
        }
