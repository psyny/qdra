import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from repositories.project_repository import ProjectRepository
from repositories.project_template_repository import ProjectTemplateRepository
from services.material_service import MaterialService
from services.recipe_service import RecipeService
from services.planning.output_planner_service import PlanningService

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
    ObjectiveMode,
    TargetRequirement,
    DomainPlanningConstraints,
    SearchParameters,
    ObjectiveFunction,
    RankingRequest,
    RankingResult,
    RankingCriterion,
    RankingCriterionType,
)

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    project_template_id: uuid.UUID  # Required as of template hub milestone


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    project_template_id: Optional[uuid.UUID]


# Planning API Models


class ParameterConstraintSpecModel(BaseModel):
    domain: str
    key: str
    operator: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    is_wildcard: bool = False


class TargetRequirementModel(BaseModel):
    quantity: float
    constraints: List[ParameterConstraintSpecModel]


class MaterialConstraintRuleModel(BaseModel):
    constraints: List[ParameterConstraintSpecModel]


class DomainPlanningConstraintsModel(BaseModel):
    do_not_expand_materials_matching: List[MaterialConstraintRuleModel] = []
    forbidden_materials_matching: List[MaterialConstraintRuleModel] = []
    forbidden_recipe_matching: List[MaterialConstraintRuleModel] = []
    max_recipe_depth: int = 10


class SearchParametersModel(BaseModel):
    max_recursion_depth: int = 20
    max_branch_width: int = 10
    allow_loops: bool = False
    max_solutions_returned: int = 10


class ObjectiveCriterionModel(BaseModel):
    kind: CriterionKind
    constraints: Optional[List[ParameterConstraintSpecModel]] = None


class ObjectiveFunctionModel(BaseModel):
    mode: ObjectiveMode = ObjectiveMode.LEXICOGRAPHIC
    criteria: List[ObjectiveCriterionModel] = []


class PlanningRequestModel(BaseModel):
    target: TargetRequirementModel
    domain_constraints: DomainPlanningConstraintsModel = DomainPlanningConstraintsModel()
    search_parameters: SearchParametersModel = SearchParametersModel()
    objective: ObjectiveFunctionModel = ObjectiveFunctionModel()
    ranking: Optional["RankingRequestModel"] = None


class RankingCriterionModel(BaseModel):
    id: str
    type: RankingCriterionType
    material_constraint: Optional[ParameterConstraintSpecModel] = None


class RankingRequestModel(BaseModel):
    max_plans_per_criterion: int = 5
    criteria: List[RankingCriterionModel] = []


class MaterialRequirementNodeModel(BaseModel):
    id: str
    kind: NodeKind
    role: MaterialRole
    quantity: float
    constraints: List[ParameterConstraintSpecModel]


class RecipeExecutionNodeModel(BaseModel):
    id: str
    kind: NodeKind
    recipe_id: uuid.UUID
    execution_count: int


class EdgeModel(BaseModel):
    from_node: str
    to_node: str
    kind: EdgeKind


class PlanGraphModel(BaseModel):
    nodes: List[dict] = []  # Can be either node type
    edges: List[EdgeModel] = []


class ObjectiveScoreModel(BaseModel):
    material_costs: dict = {}
    recipe_count: int = 0
    objective_tuple: List[float] = []


class FailureReasonModel(BaseModel):
    requirement_id: str
    reason: str


class PlanningDiagnosticsModel(BaseModel):
    nodes_explored: int = 0
    branches_pruned: int = 0
    search_time_ms: float = 0.0


class PlanCandidateModel(BaseModel):
    success: bool = True
    plan_id: str
    graph: PlanGraphModel
    root_requirements: List[MaterialRequirementNodeModel] = []
    blocked_requirements: List[FailureReasonModel] = []
    score: ObjectiveScoreModel
    diagnostics: PlanningDiagnosticsModel


class PlanningResponseModel(BaseModel):
    success: bool
    plans: List[PlanCandidateModel] = []
    rankings: List["RankingResultModel"] = []
    remaining_plan_ids: List[str] = []


class RankingResultModel(BaseModel):
    criterion_id: str
    ranked_plan_ids: List[str] = []


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    # Validate that the template exists
    template_repo = ProjectTemplateRepository(db)
    template = template_repo.get_by_id(project_data.project_template_id)
    if not template:
        raise HTTPException(status_code=400, detail="Project template not found")

    repo = ProjectRepository(db)
    project = repo.create(project_data.name, project_data.project_template_id)
    return project


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    return repo.list_all()


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


class ProjectUpdateTemplate(BaseModel):
    project_template_id: Optional[uuid.UUID] = None


@router.patch("/projects/{project_id}/template", response_model=ProjectResponse)
def update_project_template(
    project_id: uuid.UUID,
    data: ProjectUpdateTemplate,
    db: Session = Depends(get_db),
):
    """Update a project's template. Can be set to null to use abstraction display."""
    if data.project_template_id is not None:
        template_repo = ProjectTemplateRepository(db)
        template = template_repo.get_by_id(data.project_template_id)
        if not template:
            raise HTTPException(status_code=400, detail="Project template not found")

    repo = ProjectRepository(db)
    project = repo.update_template(project_id, data.project_template_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/projects/{project_id}/plan/output", response_model=PlanningResponseModel)
def plan_target(project_id: uuid.UUID, request_data: PlanningRequestModel, db: Session = Depends(get_db)):
    """Generate plan candidates for a target material requirement."""
    service = PlanningService(db)
    
    # Convert Pydantic models to domain models
    target = TargetRequirement(
        quantity=request_data.target.quantity,
        constraints=[
            ParameterConstraintSpec(
                domain=c.domain,
                key=c.key,
                operator=c.operator,
                value_string=c.value_string,
                value_number=c.value_number,
                value_boolean=c.value_boolean,
                is_wildcard=c.is_wildcard
            )
            for c in request_data.target.constraints
        ]
    )
    
    domain_constraints = DomainPlanningConstraints(
        do_not_expand_materials_matching=[
            MaterialConstraintRule(
                constraints=[
                    ParameterConstraintSpec(
                        domain=c.domain,
                        key=c.key,
                        operator=c.operator,
                        value_string=c.value_string,
                        value_number=c.value_number,
                        value_boolean=c.value_boolean,
                        is_wildcard=c.is_wildcard
                    )
                    for c in rule.constraints
                ]
            )
            for rule in request_data.domain_constraints.do_not_expand_materials_matching
        ],
        forbidden_materials_matching=[
            MaterialConstraintRule(
                constraints=[
                    ParameterConstraintSpec(
                        domain=c.domain,
                        key=c.key,
                        operator=c.operator,
                        value_string=c.value_string,
                        value_number=c.value_number,
                        value_boolean=c.value_boolean,
                        is_wildcard=c.is_wildcard
                    )
                    for c in rule.constraints
                ]
            )
            for rule in request_data.domain_constraints.forbidden_materials_matching
        ],
        forbidden_recipe_matching=[
            MaterialConstraintRule(
                constraints=[
                    ParameterConstraintSpec(
                        domain=c.domain,
                        key=c.key,
                        operator=c.operator,
                        value_string=c.value_string,
                        value_number=c.value_number,
                        value_boolean=c.value_boolean,
                        is_wildcard=c.is_wildcard
                    )
                    for c in rule.constraints
                ]
            )
            for rule in request_data.domain_constraints.forbidden_recipe_matching
        ],
        max_recipe_depth=request_data.domain_constraints.max_recipe_depth
    )
    
    search_parameters = SearchParameters(
        max_recursion_depth=request_data.search_parameters.max_recursion_depth,
        max_branch_width=request_data.search_parameters.max_branch_width,
        allow_loops=request_data.search_parameters.allow_loops,
        max_solutions_returned=request_data.search_parameters.max_solutions_returned
    )
    
    objective = ObjectiveFunction(
        mode=request_data.objective.mode,
        criteria=[
            ObjectiveCriterion(
                kind=criterion.kind,
                constraints=[
                    ParameterConstraintSpec(
                        domain=c.domain,
                        key=c.key,
                        operator=c.operator,
                        value_string=c.value_string,
                        value_number=c.value_number,
                        value_boolean=c.value_boolean,
                        is_wildcard=c.is_wildcard
                    )
                    for c in criterion.constraints
                ] if criterion.constraints else None
            )
            for criterion in request_data.objective.criteria
        ]
    )
    
    planning_request = PlanningRequest(
        project_id=project_id,
        target=target,
        domain_constraints=domain_constraints,
        search_parameters=search_parameters,
        objective=objective
    )
    
    # Convert ranking request if provided
    ranking_request = None
    if request_data.ranking:
        ranking_request = RankingRequest(
            max_plans_per_criterion=request_data.ranking.max_plans_per_criterion,
            criteria=[
                RankingCriterion(
                    id=criterion.id,
                    type=criterion.type,
                    material_constraint=ParameterConstraintSpec(
                        domain=criterion.material_constraint.domain,
                        key=criterion.material_constraint.key,
                        operator=criterion.material_constraint.operator,
                        value_string=criterion.material_constraint.value_string,
                        value_number=criterion.material_constraint.value_number,
                        value_boolean=criterion.material_constraint.value_boolean,
                        is_wildcard=criterion.material_constraint.is_wildcard
                    ) if criterion.material_constraint else None
                )
                for criterion in request_data.ranking.criteria
            ]
        )
    
    result = service.plan(planning_request, ranking_request)
    
    # Convert domain models back to Pydantic models
    def node_to_dict(node):
        if isinstance(node, MaterialRequirementNode):
            return {
                "id": node.id,
                "kind": node.kind.value,
                "role": node.role.value,
                "quantity": node.quantity,
                "constraints": [
                    {
                        "domain": c.domain,
                        "key": c.key,
                        "operator": c.operator,
                        "value_string": c.value_string,
                        "value_number": c.value_number,
                        "value_boolean": c.value_boolean,
                        "is_wildcard": c.is_wildcard
                    }
                    for c in node.constraints
                ]
            }
        elif isinstance(node, RecipeExecutionNode):
            return {
                "id": node.id,
                "kind": node.kind.value,
                "recipe_id": node.recipe_id,
                "execution_count": node.execution_count
            }
        return {}
    
    plans = []
    for plan in result.plans:
        plan_model = PlanCandidateModel(
            success=plan.success,
            plan_id=plan.plan_id,
            graph=PlanGraphModel(
                nodes=[node_to_dict(node) for node in plan.graph.nodes],
                edges=[
                    EdgeModel(
                        from_node=edge.from_node,
                        to_node=edge.to_node,
                        kind=edge.kind
                    )
                    for edge in plan.graph.edges
                ]
            ),
            root_requirements=[
                MaterialRequirementNodeModel(
                    id=req.id,
                    kind=req.kind,
                    role=req.role,
                    quantity=req.quantity,
                    constraints=[
                        ParameterConstraintSpecModel(
                            domain=c.domain,
                            key=c.key,
                            operator=c.operator,
                            value_string=c.value_string,
                            value_number=c.value_number,
                            value_boolean=c.value_boolean,
                            is_wildcard=c.is_wildcard
                        )
                        for c in req.constraints
                    ]
                )
                for req in plan.root_requirements
            ],
            blocked_requirements=[
                FailureReasonModel(
                    requirement_id=req.requirement_id,
                    reason=req.reason
                )
                for req in plan.blocked_requirements
            ],
            score=ObjectiveScoreModel(
                material_costs=plan.score.material_costs,
                recipe_count=plan.score.recipe_count,
                objective_tuple=plan.score.objective_tuple
            ),
            diagnostics=PlanningDiagnosticsModel(
                nodes_explored=plan.diagnostics.nodes_explored,
                branches_pruned=plan.diagnostics.branches_pruned,
                search_time_ms=plan.diagnostics.search_time_ms
            )
        )
        plans.append(plan_model)
    
    # Convert rankings
    rankings = [
        RankingResultModel(
            criterion_id=ranking.criterion_id,
            ranked_plan_ids=ranking.ranked_plan_ids
        )
        for ranking in result.rankings
    ]
    
    return PlanningResponseModel(
        success=result.success,
        plans=plans,
        rankings=rankings,
        remaining_plan_ids=result.remaining_plan_ids
    )
