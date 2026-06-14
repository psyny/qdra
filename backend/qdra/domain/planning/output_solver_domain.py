import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Union
from enum import Enum


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
    kind: str = "material"


@dataclass
class RecipeExecNode:
    id: str
    recipe_id: uuid.UUID
    execution_count: int = 1
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
    constraints: List[ConstraintSpec]


@dataclass
class DomainConstraints:
    do_not_expand_materials_matching: List[ConstraintRule] = field(default_factory=list)
    forbidden_materials_matching: List[ConstraintRule] = field(default_factory=list)
    forbidden_recipe_ids: List[uuid.UUID] = field(default_factory=list)
    max_recipe_depth: int = 10


@dataclass
class SearchParameters:
    max_recursion_depth: int = 20
    max_branch_width: int = 10
    allow_loops: bool = False
    max_solutions_returned: int = 10


@dataclass
class SolverRequest:
    project_id: uuid.UUID
    target: TargetSpec
    domain_constraints: DomainConstraints = field(default_factory=DomainConstraints)
    search_parameters: SearchParameters = field(default_factory=SearchParameters)


@dataclass
class PlanScore:
    recipe_count: int = 0


@dataclass
class SolvedPlan:
    plan_id: str
    graph_nodes: List[Union[MaterialNode, RecipeExecNode]]
    material_edges: List[MaterialEdge]
    recipe_edges: List[RecipeEdge]
    score: PlanScore


@dataclass
class SolverResponse:
    success: bool
    plans: List[SolvedPlan] = field(default_factory=list)
