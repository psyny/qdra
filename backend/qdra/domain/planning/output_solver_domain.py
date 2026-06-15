import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Union
from enum import Enum


SYSTEM_VARIABLE_NAMES = {"RecipeExecution", "MaterialSplit", "SourceProduction"}


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MaterialNodeType(Enum):
    """Type of material node per the output-solver graph model."""
    TARGET = "t"    # initial user-specified need
    OUTPUT = "o"    # produced by a recipe execution
    INPUT = "i"     # consumed by a recipe execution
    REQUIRES = "r"  # required by a recipe but not consumed


class RecipeEdgeType(Enum):
    PRODUCES = "p"
    CONSUMES = "c"
    REQUIRES = "r"


# ---------------------------------------------------------------------------
# Constraint spec (reused from old model but standalone here)
# ---------------------------------------------------------------------------

@dataclass
class ConstraintSpec:
    domain: str
    key: str
    operator: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    is_wildcard: bool = False


@dataclass
class ConstraintRule:
    """Rule for do_not_expand / forbidden checks."""
    constraints: List[ConstraintSpec]


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

@dataclass
class MaterialNode:
    id: str
    material_constraints: List[ConstraintSpec]
    produced_qty: float = 0.0
    consumed_qty: float = 0.0
    type: MaterialNodeType = MaterialNodeType.INPUT
    tags: List[str] = field(default_factory=list)
    rank: int = 0
    kind: str = "material"


@dataclass
class RecipeExecNode:
    id: str
    recipe_id: uuid.UUID
    execution_count: float = 1.0
    tags: List[str] = field(default_factory=list)
    rank: int = 0
    kind: str = "recipe_execution"


# ---------------------------------------------------------------------------
# Graph edges
# ---------------------------------------------------------------------------

@dataclass
class MaterialEdge:
    """Connects two material nodes: output → input/target."""
    from_node_id: str
    to_node_id: str
    qty: float


@dataclass
class RecipeEdge:
    """Connects a material node and a recipe execution node."""
    from_node_id: str
    to_node_id: str
    qty: float
    type: RecipeEdgeType   # p=produces, c=consumes, r=requires


# ---------------------------------------------------------------------------
# Request / response
# ---------------------------------------------------------------------------

@dataclass
class TargetSpec:
    quantity: float
    target_type: str = "material"  # "material" or "recipe"
    constraints: List[ConstraintSpec] = field(default_factory=list)


@dataclass
class DomainConstraints:
    do_not_expand_materials_matching: List[ConstraintRule] = field(default_factory=list)
    forbidden_materials_matching: List[ConstraintRule] = field(default_factory=list)
    forbidden_recipe_matching: List[ConstraintRule] = field(default_factory=list)
    max_recipe_depth: int = 10
    allow_partial_recipe_execution: bool = False


@dataclass
class SearchParameters:
    max_recursion_depth: int = 20
    max_branch_width: int = 10
    allow_loops: bool = False
    max_solutions_returned: int = 10
    optimization_level: int = 0


@dataclass
class DiscardedPlansStats:
    loops: int = 0
    max_recursion_depth: int = 0
    max_recipe_depth: int = 0
    forbidden_recipes: int = 0
    forbidden_materials: int = 0
    do_not_expand_materials: int = 0
    max_solutions_returned: int = 0
    no_producers_found: int = 0


@dataclass
class UserVariableDef:
    name: str
    parameter_domain: str
    parameter_key: str
    variable_type: str  # "material" or "recipe"
    # list of options (OR semantics); each option is a list of ConstraintSpec (AND semantics)
    constraints: List[List[ConstraintSpec]] = field(default_factory=list)


@dataclass
class ScoreFormulaDef:
    name: str
    formula: str


@dataclass
class ScoreRules:
    user_variables: List[UserVariableDef] = field(default_factory=list)
    score_formulas: List[ScoreFormulaDef] = field(default_factory=list)


@dataclass
class SolverRequest:
    project_id: uuid.UUID
    target: TargetSpec
    domain_constraints: DomainConstraints = field(default_factory=DomainConstraints)
    search_parameters: SearchParameters = field(default_factory=SearchParameters)
    score_rules: Optional[ScoreRules] = None


@dataclass
class SolvedPlan:
    plan_id: str
    graph_nodes: List[Union[MaterialNode, RecipeExecNode]]
    material_edges: List[MaterialEdge]
    recipe_edges: List[RecipeEdge]
    score: Dict[str, float]


@dataclass
class EntityData:
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    parameters: List[ConstraintSpec] = field(default_factory=list)


@dataclass
class Entities:
    materials: Dict[uuid.UUID, EntityData] = field(default_factory=dict)
    recipes: Dict[uuid.UUID, EntityData] = field(default_factory=dict)


@dataclass
class SolverResponse:
    success: bool
    plans: List[SolvedPlan] = field(default_factory=list)
    entities: Entities = field(default_factory=Entities)
    discarded_plans_stats: DiscardedPlansStats = field(default_factory=DiscardedPlansStats)
