import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from infrastructure.db.models import PlanningRun
from domain.constraints import ConstraintSpec, ConstraintRule
from domain.planning.output_solver_domain import (
    TargetSpec,
    DomainConstraints, SearchParameters, SolverRequest,
    UserVariableDef, ScoreFormulaDef, ScoreRules,
)

router = APIRouter(prefix="/api/planning-runs")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CreatePlanningRunRequest(BaseModel):
    name: Optional[str] = None
    type: str
    status: str = "pending"
    input: Optional[Dict[str, Any]] = None


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
    target_type: str = "material"
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


class OutputSolverRunRequest(BaseModel):
    project_id: uuid.UUID
    target: TargetSpecModel
    domain_constraints: DomainConstraintsModel = DomainConstraintsModel()
    search_parameters: SearchParametersModel = SearchParametersModel()
    score_rules: Optional[ScoreRulesModel] = None
    name: Optional[str] = None


class PlanningRunResponse(BaseModel):
    id: uuid.UUID
    name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str
    type: str
    input: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    model_config = {"from_attributes": True}


class PlanningRunListResponse(BaseModel):
    id: uuid.UUID
    name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str
    type: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("", response_model=PlanningRunResponse)
def create_planning_run(
    request: CreatePlanningRunRequest,
    db: Session = Depends(get_db),
):
    """Create a new planning run."""
    planning_run = PlanningRun(
        name=request.name,
        type=request.type,
        status=request.status,
        input=request.input,
    )
    db.add(planning_run)
    db.commit()
    db.refresh(planning_run)
    return planning_run


@router.get("", response_model=List[PlanningRunListResponse])
def list_planning_runs(
    type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all planning runs without results (to avoid traffic bloat). Can filter by type and status."""
    query = db.query(PlanningRun)
    if type is not None:
        query = query.filter(PlanningRun.type == type)
    if status is not None:
        query = query.filter(PlanningRun.status == status)
    planning_runs = query.all()
    return planning_runs


@router.get("/{run_id}", response_model=PlanningRunListResponse)
def get_planning_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get a single planning run without results via its ID."""
    planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
    if not planning_run:
        raise HTTPException(status_code=404, detail="Planning run not found")
    return planning_run


@router.get("/{run_id}/with-results", response_model=PlanningRunResponse)
def get_planning_run_with_results(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get a single planning run with results via its ID."""
    planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
    if not planning_run:
        raise HTTPException(status_code=404, detail="Planning run not found")
    return planning_run


@router.put("/{run_id}", response_model=PlanningRunResponse)
def update_planning_run(
    run_id: uuid.UUID,
    status: Optional[str] = None,
    input: Optional[Dict[str, Any]] = None,
    started_at: Optional[datetime] = None,
    finished_at: Optional[datetime] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Update a planning run's status, input, timing, result, and/or error."""
    planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
    if not planning_run:
        raise HTTPException(status_code=404, detail="Planning run not found")
    
    if status is not None:
        planning_run.status = status
    if input is not None:
        planning_run.input = input
    if started_at is not None:
        planning_run.started_at = started_at
    if finished_at is not None:
        planning_run.finished_at = finished_at
    if result is not None:
        planning_run.result = result
    if error is not None:
        planning_run.error = error
    
    db.commit()
    db.refresh(planning_run)
    return planning_run


@router.post("/output-solver/runs", response_model=PlanningRunResponse)
def create_output_solver_run(
    request: OutputSolverRunRequest,
    db: Session = Depends(get_db),
):
    """Create an output solver planning run (async execution)."""
    
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
        quantity=request.target.quantity,
        target_type=request.target.target_type,
        constraints=[to_spec(c) for c in request.target.constraints],
    )
    dc = request.domain_constraints
    domain_constraints = DomainConstraints(
        do_not_expand_materials_matching=[to_rule(r) for r in dc.do_not_expand_materials_matching],
        forbidden_materials_matching=[to_rule(r) for r in dc.forbidden_materials_matching],
        forbidden_recipe_matching=[to_rule(r) for r in dc.forbidden_recipe_matching],
        required_materials_matching=[to_rule(r) for r in dc.required_materials_matching],
        required_recipe_matching=[to_rule(r) for r in dc.required_recipe_matching],
        max_recipe_depth=dc.max_recipe_depth,
        allow_partial_recipe_execution=dc.allow_partial_recipe_execution,
    )
    sp = request.search_parameters
    search_parameters = SearchParameters(
        max_recursion_depth=sp.max_recursion_depth,
        max_branch_width=sp.max_branch_width,
        allow_loops=sp.allow_loops,
        max_solutions_returned=sp.max_solutions_returned,
        optimization_level=sp.optimization_level,
    )

    score_rules = None
    if request.score_rules is not None:
        sr = request.score_rules
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
        project_id=request.project_id,
        target=target,
        domain_constraints=domain_constraints,
        search_parameters=search_parameters,
        score_rules=score_rules,
    )

    # Convert SolverRequest to dict for JSONB storage
    input_dict = {
        "project_id": str(solver_request.project_id),
        "target": {
            "quantity": solver_request.target.quantity,
            "target_type": solver_request.target.target_type,
            "constraints": [
                {
                    "domain": c.domain,
                    "key": c.key,
                    "operator": getattr(c, 'operator', '='),
                    "value_string": c.value_string,
                    "value_number": c.value_number,
                    "value_boolean": c.value_boolean,
                    "is_wildcard": getattr(c, 'is_wildcard', False),
                }
                for c in solver_request.target.constraints
            ],
        },
        "domain_constraints": {
            "do_not_expand_materials_matching": [
                {
                    "constraints": [
                        {
                            "domain": c.domain,
                            "key": c.key,
                            "operator": c.operator,
                            "value_string": c.value_string,
                            "value_number": c.value_number,
                            "value_boolean": c.value_boolean,
                            "is_wildcard": c.is_wildcard,
                        }
                        for c in rule.constraints
                    ]
                }
                for rule in solver_request.domain_constraints.do_not_expand_materials_matching
            ],
            "forbidden_materials_matching": [
                {
                    "constraints": [
                        {
                            "domain": c.domain,
                            "key": c.key,
                            "operator": c.operator,
                            "value_string": c.value_string,
                            "value_number": c.value_number,
                            "value_boolean": c.value_boolean,
                            "is_wildcard": c.is_wildcard,
                        }
                        for c in rule.constraints
                    ]
                }
                for rule in solver_request.domain_constraints.forbidden_materials_matching
            ],
            "forbidden_recipe_matching": [
                {
                    "constraints": [
                        {
                            "domain": c.domain,
                            "key": c.key,
                            "operator": c.operator,
                            "value_string": c.value_string,
                            "value_number": c.value_number,
                            "value_boolean": c.value_boolean,
                            "is_wildcard": c.is_wildcard,
                        }
                        for c in rule.constraints
                    ]
                }
                for rule in solver_request.domain_constraints.forbidden_recipe_matching
            ],
            "required_materials_matching": [
                {
                    "constraints": [
                        {
                            "domain": c.domain,
                            "key": c.key,
                            "operator": c.operator,
                            "value_string": c.value_string,
                            "value_number": c.value_number,
                            "value_boolean": c.value_boolean,
                            "is_wildcard": c.is_wildcard,
                        }
                        for c in rule.constraints
                    ]
                }
                for rule in solver_request.domain_constraints.required_materials_matching
            ],
            "required_recipe_matching": [
                {
                    "constraints": [
                        {
                            "domain": c.domain,
                            "key": c.key,
                            "operator": c.operator,
                            "value_string": c.value_string,
                            "value_number": c.value_number,
                            "value_boolean": c.value_boolean,
                            "is_wildcard": c.is_wildcard,
                        }
                        for c in rule.constraints
                    ]
                }
                for rule in solver_request.domain_constraints.required_recipe_matching
            ],
            "max_recipe_depth": solver_request.domain_constraints.max_recipe_depth,
            "allow_partial_recipe_execution": solver_request.domain_constraints.allow_partial_recipe_execution,
        },
        "search_parameters": {
            "max_recursion_depth": solver_request.search_parameters.max_recursion_depth,
            "max_branch_width": solver_request.search_parameters.max_branch_width,
            "allow_loops": solver_request.search_parameters.allow_loops,
            "max_solutions_returned": solver_request.search_parameters.max_solutions_returned,
            "optimization_level": solver_request.search_parameters.optimization_level,
        },
    }

    if score_rules:
        input_dict["score_rules"] = {
            "user_variables": [
                {
                    "name": v.name,
                    "parameter_domain": v.parameter_domain,
                    "parameter_key": v.parameter_key,
                    "constraints": [
                        {
                            "constraints": [
                                {
                                    "domain": c.domain,
                                    "key": c.key,
                                    "operator": getattr(c, 'operator', '='),
                                    "value_string": c.value_string,
                                    "value_number": c.value_number,
                                    "value_boolean": c.value_boolean,
                                    "is_wildcard": getattr(c, 'is_wildcard', False),
                                }
                                for c in rule.constraints
                            ]
                        }
                        for rule in v.constraints
                    ],
                }
                for v in score_rules.user_variables
            ],
            "score_formulas": [
                {"name": f.name, "formula": f.formula}
                for f in score_rules.score_formulas
            ],
        }

    planning_run = PlanningRun(
        name=request.name,
        type="output_solver",
        status="pending",
        input=input_dict,
    )
    db.add(planning_run)
    db.commit()
    db.refresh(planning_run)
    return planning_run
