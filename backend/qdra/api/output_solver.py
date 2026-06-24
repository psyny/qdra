import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from services.planning.output_solver_service import OutputSolverService
from domain.constraints import ConstraintSpec, ConstraintRule
from domain.planning.output_solver_domain import (
    TargetSpec,
    DomainConstraints, SearchParameters, SolverRequest,
    UserVariableDef, ScoreFormulaDef, ScoreRules,
    MaterialNodeType, RecipeEdgeType,
    Entities, EntityData,
)
from infrastructure.security.permission_checker import require_can_run_plan

router = APIRouter(prefix="/api")


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
    target_type: str = "material"  # "material" or "recipe"
    constraints: List[ConstraintSpecModel] = []


class ConstraintRuleModel(BaseModel):
    constraints: List[ConstraintSpecModel]


class DomainConstraintsModel(BaseModel):
    do_not_expand_materials_matching: List[ConstraintRuleModel] = []
    forbidden_materials_matching: List[ConstraintRuleModel] = []
    forbidden_recipe_matching: List[ConstraintRuleModel] = []
    required_materials_matching: List[ConstraintRuleModel] = []
    required_recipe_matching: List[ConstraintRuleModel] = []
    max_recipe_depth: int = 10
    allow_partial_recipe_execution: bool = False


class SearchParametersModel(BaseModel):
    max_recursion_depth: int = 20
    max_branch_width: int = 10
    allow_loops: bool = False
    max_solutions_returned: int = 10
    optimization_level: int = 0


class ConstraintSpecForVarModel(BaseModel):
    domain: str
    key: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None


class UserVariableDefModel(BaseModel):
    name: str
    parameter_domain: str
    parameter_key: str
    constraints: List[ConstraintRuleModel] = []


class ScoreFormulaDefModel(BaseModel):
    name: str
    formula: str


class ScoreRulesModel(BaseModel):
    user_variables: List[UserVariableDefModel] = []
    score_formulas: List[ScoreFormulaDefModel] = []


class SolverRequestModel(BaseModel):
    target: TargetSpecModel
    domain_constraints: DomainConstraintsModel = DomainConstraintsModel()
    search_parameters: SearchParametersModel = SearchParametersModel()
    score_rules: Optional[ScoreRulesModel] = None


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class MaterialNodeModel(BaseModel):
    id: str
    kind: str
    type: str
    material_id: Optional[str] = None
    produced_qty: float
    consumed_qty: float
    tags: List[str] = []


class RecipeExecNodeModel(BaseModel):
    id: str
    kind: str
    recipe_id: uuid.UUID
    execution_count: float


class EdgeModel(BaseModel):
    from_node_id: str
    to_node_id: str
    qty: float
    edge_type: str


class GraphModel(BaseModel):
    nodes: List[dict] = []
    edges: List[EdgeModel] = []


class EntityDataModel(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    parameters: List[ConstraintSpecModel] = []


class EntitiesModel(BaseModel):
    materials: Dict[uuid.UUID, EntityDataModel] = {}
    recipes: Dict[uuid.UUID, EntityDataModel] = {}


class SolvedPlanModel(BaseModel):
    plan_id: str
    graph: GraphModel
    score: Dict[str, float]


class DiscardedPlansStatsModel(BaseModel):
    loops: int = 0
    max_recursion_depth: int = 0
    max_recipe_depth: int = 0
    forbidden_recipes: int = 0
    forbidden_materials: int = 0
    do_not_expand_materials: int = 0
    max_solutions_returned: int = 0
    no_producers_found: int = 0


class SolverResponseModel(BaseModel):
    success: bool
    plans: List[SolvedPlanModel] = []
    entities: EntitiesModel = EntitiesModel()
    discarded_plans_stats: DiscardedPlansStatsModel = DiscardedPlansStatsModel()


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/projects/{project_id}/solver/output", response_model=SolverResponseModel)
def solve_output(
    project_id: uuid.UUID,
    request_data: SolverRequestModel,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(require_can_run_plan),
):
    """Run the output solver algorithm to produce plan graphs."""

    def to_spec(m: ConstraintSpecModel) -> ConstraintSpec:
        # Handle missing operator field with default
        operator = getattr(m, 'operator', '=')
        is_wildcard = getattr(m, 'is_wildcard', False)
        return ConstraintSpec(
            domain=m.domain, key=m.key, operator=operator,
            value_string=m.value_string, value_number=m.value_number,
            value_boolean=m.value_boolean, is_wildcard=is_wildcard,
        )

    def to_rule(m: ConstraintRuleModel) -> ConstraintRule:
        return ConstraintRule(constraints=[to_spec(c) for c in m.constraints])

    target = TargetSpec(
        quantity=request_data.target.quantity,
        target_type=request_data.target.target_type,
        constraints=[to_spec(c) for c in request_data.target.constraints],
    )
    dc = request_data.domain_constraints
    domain_constraints = DomainConstraints(
        do_not_expand_materials_matching=[to_rule(r) for r in dc.do_not_expand_materials_matching],
        forbidden_materials_matching=[to_rule(r) for r in dc.forbidden_materials_matching],
        forbidden_recipe_matching=[to_rule(r) for r in dc.forbidden_recipe_matching],
        required_materials_matching=[to_rule(r) for r in dc.required_materials_matching],
        required_recipe_matching=[to_rule(r) for r in dc.required_recipe_matching],
        max_recipe_depth=dc.max_recipe_depth,
        allow_partial_recipe_execution=dc.allow_partial_recipe_execution,
    )
    sp = request_data.search_parameters
    search_parameters = SearchParameters(
        max_recursion_depth=sp.max_recursion_depth,
        max_branch_width=sp.max_branch_width,
        allow_loops=sp.allow_loops,
        max_solutions_returned=sp.max_solutions_returned,
        optimization_level=sp.optimization_level,
    )

    score_rules = None
    if request_data.score_rules is not None:
        sr = request_data.score_rules
        user_vars = [
            UserVariableDef(
                name=v.name,
                parameter_domain=v.parameter_domain,
                parameter_key=v.parameter_key,
                constraints=[to_rule(rule) for rule in v.constraints],
            )
            for v in sr.user_variables
        ]
        formulas = [
            ScoreFormulaDef(name=f.name, formula=f.formula)
            for f in sr.score_formulas
        ]
        score_rules = ScoreRules(user_variables=user_vars, score_formulas=formulas)

    solver_request = SolverRequest(
        project_id=project_id,
        target=target,
        domain_constraints=domain_constraints,
        search_parameters=search_parameters,
        score_rules=score_rules,
    )

    service = OutputSolverService(db)
    try:
        result = service.solve(solver_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
                    "tags": n.tags,
                })
            else:
                nodes.append({
                    "id": n.id,
                    "kind": n.kind,
                    "type": n.type.value,
                    "material_id": str(n.material_id) if n.material_id else None,
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
            score=plan.score,
        ))

    entities_data = result.entities
    entities_model = EntitiesModel(
        materials={
            k: EntityDataModel(
                id=v.id, project_id=v.project_id, created_at=v.created_at,
                parameters=[ConstraintSpecModel(
                    domain=p.domain, key=p.key, operator=p.operator,
                    value_string=p.value_string, value_number=p.value_number,
                    value_boolean=p.value_boolean, is_wildcard=p.is_wildcard,
                ) for p in v.parameters]
            )
            for k, v in entities_data.materials.items()
        },
        recipes={
            k: EntityDataModel(
                id=v.id, project_id=v.project_id, created_at=v.created_at,
                parameters=[ConstraintSpecModel(
                    domain=p.domain, key=p.key, operator=p.operator,
                    value_string=p.value_string, value_number=p.value_number,
                    value_boolean=p.value_boolean, is_wildcard=p.is_wildcard,
                ) for p in v.parameters]
            )
            for k, v in entities_data.recipes.items()
        },
    )

    return SolverResponseModel(
        success=result.success,
        plans=plans,
        entities=entities_model,
        discarded_plans_stats=DiscardedPlansStatsModel(
            loops=result.discarded_plans_stats.loops,
            max_recursion_depth=result.discarded_plans_stats.max_recursion_depth,
            max_recipe_depth=result.discarded_plans_stats.max_recipe_depth,
            forbidden_recipes=result.discarded_plans_stats.forbidden_recipes,
            forbidden_materials=result.discarded_plans_stats.forbidden_materials,
            do_not_expand_materials=result.discarded_plans_stats.do_not_expand_materials,
            max_solutions_returned=result.discarded_plans_stats.max_solutions_returned,
            no_producers_found=result.discarded_plans_stats.no_producers_found,
        ),
    )
