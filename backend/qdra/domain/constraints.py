"""Canonical constraint definitions used across the system."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Operator(str, Enum):
    """Comparison operators for constraints."""
    EQ = "="
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    IN = "in"
    EXISTS = "exists"


@dataclass
class ConstraintSpec:
    """Canonical constraint specification for entity filtering.
    
    This is the domain model used throughout the system for constraint logic.
    The database model (ParameterConstraint) is only for persistence.
    """
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
    constraints: list[ConstraintSpec]
