import uuid
from typing import List, Optional, Union

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from services.planning.output_solver_service import OutputSolverService
from domain.planning.output_solver_domain import (
    ConstraintSpec, ConstraintRule, TargetSpec,
    DomainConstraints, SearchParameters, SolverRequest,
    MaterialNodeType, RecipeEdgeType,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ConstraintSpecModel(BaseModel):
    domain: str
    key: str
    operator: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    is_wildcard: bool = False


class TargetSpecModel(BaseModel):
    quantity: float
    constraints: List[ConstraintSpecModel]


class ConstraintRuleModel(BaseModel):
    constraints: List[ConstraintSpecModel]


class DomainConstraintsModel(BaseModel):
    do_not_expand_materials_matching: List[ConstraintRuleModel] = []
    forbidden_materials_matching: List[ConstraintRuleModel] = []
    forbidden_recipe_ids: List[uuid.UUID] = []
    max_recipe_depth: int = 10


class SearchParametersModel(BaseModel):
    max_recursion_depth: int = 20
    max_branch_width: int = 10
    allow_loops: bool = False
    max_solutions_returned: int = 10


class SolverRequestModel(BaseModel):
    target: TargetSpecModel
    domain_constraints: DomainConstraintsModel = DomainConstraintsModel()
    search_parameters: SearchParametersModel = SearchParametersModel()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class MaterialNodeModel(BaseModel):
    id: str
    kind: str
    type: str
    material_constraints: List[ConstraintSpecModel]
    produced_qty: float
    consumed_qty: float
    tags: List[str] = []


class RecipeExecNodeModel(BaseModel):
    id: str
    kind: str
    recipe_id: uuid.UUID
    execution_count: int


class EdgeModel(BaseModel):
    from_node_id: str
    to_node_id: str
    qty: float
    edge_type: str


class GraphModel(BaseModel):
    nodes: List[dict] = []
    edges: List[EdgeModel] = []


class PlanScoreModel(BaseModel):
    recipe_count: int = 0


class SolvedPlanModel(BaseModel):
    plan_id: str
    graph: GraphModel
    score: PlanScoreModel


class SolverResponseModel(BaseModel):
    success: bool
    plans: List[SolvedPlanModel] = []


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/projects/{project_id}/solver/output", response_model=SolverResponseModel)
def solve_output(
    project_id: uuid.UUID,
    request_data: SolverRequestModel,
    db: Session = Depends(get_db),
):
    """Run the output solver algorithm to produce plan graphs."""

    def to_spec(m: ConstraintSpecModel) -> ConstraintSpec:
        return ConstraintSpec(
            domain=m.domain, key=m.key, operator=m.operator,
            value_string=m.value_string, value_number=m.value_number,
            value_boolean=m.value_boolean, is_wildcard=m.is_wildcard,
        )

    def to_rule(m: ConstraintRuleModel) -> ConstraintRule:
        return ConstraintRule(constraints=[to_spec(c) for c in m.constraints])

    target = TargetSpec(
        quantity=request_data.target.quantity,
        constraints=[to_spec(c) for c in request_data.target.constraints],
    )
    dc = request_data.domain_constraints
    domain_constraints = DomainConstraints(
        do_not_expand_materials_matching=[to_rule(r) for r in dc.do_not_expand_materials_matching],
        forbidden_materials_matching=[to_rule(r) for r in dc.forbidden_materials_matching],
        forbidden_recipe_ids=dc.forbidden_recipe_ids,
        max_recipe_depth=dc.max_recipe_depth,
    )
    sp = request_data.search_parameters
    search_parameters = SearchParameters(
        max_recursion_depth=sp.max_recursion_depth,
        max_branch_width=sp.max_branch_width,
        allow_loops=sp.allow_loops,
        max_solutions_returned=sp.max_solutions_returned,
    )

    solver_request = SolverRequest(
        project_id=project_id,
        target=target,
        domain_constraints=domain_constraints,
        search_parameters=search_parameters,
    )

    service = OutputSolverService(db)
    result = service.solve(solver_request)

    plans = []
    for plan in result.plans:
        nodes = []
        for n in plan.graph_nodes:
            if hasattr(n, "recipe_id"):
                nodes.append({
                    "id": n.id,
                    "kind": n.kind,
                    "recipe_id": str(n.recipe_id),
                    "execution_count": n.execution_count,
                })
            else:
                nodes.append({
                    "id": n.id,
                    "kind": n.kind,
                    "type": n.type.value,
                    "material_constraints": [
                        {
                            "domain": c.domain, "key": c.key, "operator": c.operator,
                            "value_string": c.value_string, "value_number": c.value_number,
                            "value_boolean": c.value_boolean, "is_wildcard": c.is_wildcard,
                        }
                        for c in n.material_constraints
                    ],
                    "produced_qty": n.produced_qty,
                    "consumed_qty": n.consumed_qty,
                    "tags": n.tags,
                })

        edges = []
        for e in plan.material_edges:
            edges.append(EdgeModel(from_node_id=e.from_node_id, to_node_id=e.to_node_id, qty=e.qty, edge_type="material"))
        for e in plan.recipe_edges:
            edges.append(EdgeModel(from_node_id=e.from_node_id, to_node_id=e.to_node_id, qty=e.qty, edge_type=e.type.value))

        plans.append(SolvedPlanModel(
            plan_id=plan.plan_id,
            graph=GraphModel(nodes=nodes, edges=edges),
            score=PlanScoreModel(
                recipe_count=plan.score.recipe_count,
            ),
        ))

    return SolverResponseModel(success=result.success, plans=plans)
