import copy
import math
import uuid
from typing import List, Dict, Optional, Set, Tuple, FrozenSet
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from models.slot import SlotKind
from repositories.recipe_repository import RecipeRepository
from repositories.slot_repository import SlotRepository
from repositories.option_repository import OptionRepository
from repositories.parameter_constraint_repository import ParameterConstraintRepository
from repositories.project_repository import ProjectRepository

from domain.planning.output_solver_domain import (
    MaterialNode, RecipeExecNode, MaterialEdge, RecipeEdge,
    MaterialNodeType, RecipeEdgeType, ConstraintSpec, ConstraintRule,
    PlanScore, SolvedPlan, SolverRequest, SolverResponse,
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


class OutputSolverService:
    def __init__(self, db: Session):
        self.db = db
        self.recipe_repo = RecipeRepository(db)
        self.slot_repo = SlotRepository(db)
        self.option_repo = OptionRepository(db)
        self.constraint_repo = ParameterConstraintRepository(db)
        self.project_repo = ProjectRepository(db)

    def solve(self, request: SolverRequest) -> SolverResponse:
        if not self.project_repo.get_by_id(request.project_id):
            return SolverResponse(success=False)

        recipes = self.recipe_repo.list_by_project(request.project_id)
        recipe_structures = {r.id: self._load_recipe_structure(r.id) for r in recipes}

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
        self._explore(initial, recipe_structures, request, plans, seen_fps, frozenset())

        for i, plan in enumerate(plans):
            plan.plan_id = f"plan_{i:03d}"
            self._tag_nodes(plan)
        return SolverResponse(success=True, plans=plans)

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

    def _explore(self, state, recipe_structures, request, plans, seen_fps, ancestor_sigs):
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
            self._emit_plan(state, plans, seen_fps, request.target.constraints)
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
            self._explore(branch, recipe_structures, request, plans, seen_fps, ancestor_sigs)
            return

        if self._matches_rule(current.material_constraints, request.domain_constraints.do_not_expand_materials_matching):
            self._explore(state, recipe_structures, request, plans, seen_fps, ancestor_sigs)
            return

        if self._matches_rule(current.material_constraints, request.domain_constraints.forbidden_materials_matching):
            return

        producers = self._find_producers(
            current.material_constraints, recipe_structures,
            request.domain_constraints.forbidden_recipe_ids,
        )

        if not producers:
            self._explore(state, recipe_structures, request, plans, seen_fps, ancestor_sigs)
            return

        producers = producers[: request.search_parameters.max_branch_width]
        new_sigs = ancestor_sigs | {sig}

        for recipe_id, produces_option in producers:
            if len(plans) >= request.search_parameters.max_solutions_returned:
                return
            branch = state.clone()
            self._apply_recipe(branch, current_id, recipe_id, produces_option, recipe_structures)
            branch.recipe_depth += 1
            self._explore(branch, recipe_structures, request, plans, seen_fps, new_sigs)

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

    def _emit_plan(self, state, plans, seen_fps, target_constraints):
        fp = self._fingerprint(state)
        if fp in seen_fps:
            return
        seen_fps.add(fp)

        recipe_count = sum(n.execution_count for n in state.recipe_nodes.values())
        all_nodes = list(state.material_nodes.values()) + list(state.recipe_nodes.values())

        plans.append(SolvedPlan(
            plan_id="",
            graph_nodes=all_nodes,
            material_edges=list(state.material_edges),
            recipe_edges=list(state.recipe_edges),
            score=PlanScore(recipe_count=recipe_count),
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
        return ConstraintSpec(
            domain=c.domain, key=c.key, operator=c.operator,
            value_string=c.value_string, value_number=c.value_number,
            value_boolean=c.value_boolean, is_wildcard=c.is_wildcard,
        )

    @staticmethod
    def print_plan_graph(data: dict) -> None:
        print("\n" + "=" * 60)
        print(f"SOLVER OUTPUT  success={data.get('success')}  plans={len(data.get('plans', []))}")
        for i, plan in enumerate(data.get("plans", []), 1):
            print(f"\n--- Plan {i}: {plan.get('plan_id')} ---")
            graph = plan.get("graph", {})
            for n in graph.get("nodes", []):
                if n.get("kind") == "recipe_execution":
                    print(f"  [R] {n['id']} recipe={n.get('recipe_id')} exec={n.get('execution_count')}")
                else:
                    cs = ", ".join(f"{c['key']}={c.get('value_string','?')}" for c in n.get("material_constraints", []))
                    tags = n.get("tags", [])
                    print(f"  [M] {n['id']} type={n.get('type')} {cs} prod={n.get('produced_qty')} cons={n.get('consumed_qty')} tags={tags}")
            for e in graph.get("edges", []):
                print(f"  {e.get('from_node_id')} --[{e.get('edge_type','?')}:{e.get('qty')}]--> {e.get('to_node_id')}")
            score = plan.get("score", {})
            print(f"  score: recipe_count={score.get('recipe_count')}")
        print("=" * 60 + "\n")
