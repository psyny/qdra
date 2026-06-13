import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class NodeKind(Enum):
    MATERIAL_REQUIREMENT = "material_requirement"
    RECIPE_EXECUTION = "recipe_execution"


class MaterialRole(Enum):
    TARGET = "target"
    ROOT_REQUIREMENT = "root_requirement"
    INTERMEDIATE = "intermediate"
    PRODUCED = "produced"
    EXTERNAL_REQUIREMENT = "external_requirement"


class EdgeKind(Enum):
    CONSUMES = "consumes"
    REQUIRES = "requires"
    PRODUCES = "produces"
    SATISFIES = "satisfies"


class ObjectiveMode(Enum):
    LEXICOGRAPHIC = "lexicographic"


class CriterionKind(Enum):
    MATERIAL = "material"
    RECIPE_COUNT = "recipe_count"
    RECIPE_TYPES = "recipe_types"
    GRAPH_DEPTH = "graph_depth"


class RankingCriterionType(Enum):
    MINIMIZE_MATERIAL_REQUIREMENT = "minimize_material_requirement"
    MINIMIZE_RECIPE_EXECUTIONS = "minimize_recipe_executions"
    MINIMIZE_RECIPE_TYPES = "minimize_recipe_types"
    MINIMIZE_GRAPH_DEPTH = "minimize_graph_depth"


@dataclass
class ParameterConstraintSpec:
    """Runtime-only constraint specification."""
    domain: str
    key: str
    operator: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    is_wildcard: bool = False


@dataclass
class TargetRequirement:
    """Target material requirement."""
    quantity: float
    constraints: List[ParameterConstraintSpec]


@dataclass
class MaterialConstraintRule:
    """Rule for matching materials (do-not-expand or forbidden)."""
    constraints: List[ParameterConstraintSpec]


@dataclass
class DomainPlanningConstraints:
    """Domain-level planning constraints."""
    do_not_expand_materials_matching: List[MaterialConstraintRule] = field(default_factory=list)
    forbidden_materials_matching: List[MaterialConstraintRule] = field(default_factory=list)
    forbidden_recipe_ids: List[uuid.UUID] = field(default_factory=list)
    max_recipe_depth: int = 10


@dataclass
class SearchParameters:
    """Search behavior parameters."""
    max_recursion_depth: int = 20
    max_branch_width: int = 10
    allow_loops: bool = False
    max_solutions_returned: int = 10


@dataclass
class ObjectiveCriterion:
    """Single objective criterion."""
    kind: CriterionKind
    constraints: Optional[List[ParameterConstraintSpec]] = None  # For material kind


@dataclass
class ObjectiveFunction:
    """Objective function for plan ranking."""
    mode: ObjectiveMode = ObjectiveMode.LEXICOGRAPHIC
    criteria: List[ObjectiveCriterion] = field(default_factory=list)


@dataclass
class PlanningRequest:
    """Complete planning request."""
    project_id: uuid.UUID
    target: TargetRequirement
    domain_constraints: DomainPlanningConstraints = field(default_factory=DomainPlanningConstraints)
    search_parameters: SearchParameters = field(default_factory=SearchParameters)
    objective: ObjectiveFunction = field(default_factory=ObjectiveFunction)


@dataclass
class MaterialRequirementNode:
    """Material requirement node in plan graph."""
    id: str
    kind: NodeKind = NodeKind.MATERIAL_REQUIREMENT
    role: MaterialRole = MaterialRole.INTERMEDIATE
    quantity: float = 1.0
    constraints: List[ParameterConstraintSpec] = field(default_factory=list)


@dataclass
class RecipeExecutionNode:
    """Recipe execution node in plan graph."""
    id: str
    recipe_id: uuid.UUID
    kind: NodeKind = NodeKind.RECIPE_EXECUTION
    execution_count: int = 1


@dataclass
class Edge:
    """Edge in plan graph."""
    from_node: str
    to_node: str
    kind: EdgeKind


@dataclass
class PlanGraph:
    """Plan execution graph."""
    nodes: List[Any] = field(default_factory=list)  # MaterialRequirementNode or RecipeExecutionNode
    edges: List[Edge] = field(default_factory=list)


@dataclass
class ObjectiveScore:
    """Score for a plan candidate."""
    material_costs: Dict[str, float] = field(default_factory=dict)
    recipe_count: int = 0
    objective_tuple: List[float] = field(default_factory=list)


@dataclass
class FailureReason:
    """Reason for a blocked requirement."""
    requirement_id: str
    reason: str


@dataclass
class PlanningDiagnostics:
    """Diagnostic information about planning."""
    nodes_explored: int = 0
    branches_pruned: int = 0
    search_time_ms: float = 0.0


@dataclass
class PlanCandidate:
    """A complete plan candidate."""
    success: bool = True
    plan_id: str = ""
    graph: PlanGraph = field(default_factory=PlanGraph)
    root_requirements: List[MaterialRequirementNode] = field(default_factory=list)
    blocked_requirements: List[FailureReason] = field(default_factory=list)
    score: ObjectiveScore = field(default_factory=ObjectiveScore)
    diagnostics: PlanningDiagnostics = field(default_factory=PlanningDiagnostics)


@dataclass
class PlanningResponse:
    """Response from planning service."""
    success: bool
    plans: List[PlanCandidate] = field(default_factory=list)
    rankings: List["RankingResult"] = field(default_factory=list)
    remaining_plan_ids: List[str] = field(default_factory=list)


@dataclass
class MaterialRequirementSummary:
    """Summary of a material requirement in a plan."""
    constraint: ParameterConstraintSpec
    quantity: float


@dataclass
class PlanSummary:
    """Summary metrics for a plan used in ranking."""
    plan_id: str
    recipe_execution_count: int = 0
    recipe_type_count: int = 0
    graph_depth: int = 0
    material_requirements: List[MaterialRequirementSummary] = field(default_factory=list)


@dataclass
class RankingCriterion:
    """A single ranking criterion."""
    id: str
    type: RankingCriterionType
    material_constraint: Optional[ParameterConstraintSpec] = None  # For material-based criteria


@dataclass
class RankingRequest:
    """Request for plan ranking."""
    max_plans_per_criterion: int = 5
    criteria: List[RankingCriterion] = field(default_factory=list)


@dataclass
class RankingResult:
    """Result of ranking plans by a criterion."""
    criterion_id: str
    ranked_plan_ids: List[str] = field(default_factory=list)


@dataclass
class MemoizationCacheKey:
    """Key for memoization cache."""
    target_constraints: List[ParameterConstraintSpec]
    target_quantity: float
    domain_constraints: DomainPlanningConstraints
    search_depth_remaining: int
    forbidden_recipe_ids: List[uuid.UUID]
    forbidden_materials: List[MaterialConstraintRule]
    do_not_expand_materials: List[MaterialConstraintRule]
    allow_loops: bool


@dataclass
class MemoizedPlanningResult:
    """Cached result of a planning subproblem."""
    success: bool
    candidate_subplans: List[PlanCandidate] = field(default_factory=list)
