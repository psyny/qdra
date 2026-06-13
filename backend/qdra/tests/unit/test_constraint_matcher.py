from dataclasses import dataclass
from enum import Enum
from typing import Optional

from qdra.services.constraint_matcher import ConstraintMatcher


class Operator(str, Enum):
    EQ = "="
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    IN = "in"
    EXISTS = "exists"


@dataclass
class Parameter:
    domain: str
    key: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None


@dataclass
class ParameterConstraint:
    domain: str
    key: str
    operator: Operator
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    is_wildcard: bool = False


def test_constraint_exists_matches():
    """Test that exists operator matches when parameter exists."""
    parameter = Parameter(
        domain="classification", key="metal", value_boolean=True
    )
    constraint = ParameterConstraint(
        domain="classification", key="metal", operator=Operator.EXISTS
    )

    assert ConstraintMatcher.matches(parameter, constraint) is True


def test_constraint_exists_no_match():
    """Test that exists operator doesn't match when parameter doesn't have value."""
    parameter = Parameter(
        domain="classification", key="metal", value_string=None, value_number=None, value_boolean=None
    )
    constraint = ParameterConstraint(
        domain="classification", key="metal", operator=Operator.EXISTS
    )

    assert ConstraintMatcher.matches(parameter, constraint) is False


def test_constraint_gte_matches():
    """Test that >= operator matches when value is greater or equal."""
    parameter = Parameter(domain="stat", key="quality", value_number=78)
    constraint = ParameterConstraint(
        domain="stat", key="quality", operator=Operator.GTE, value_number=70
    )

    assert ConstraintMatcher.matches(parameter, constraint) is True


def test_constraint_gte_no_match():
    """Test that >= operator doesn't match when value is less."""
    parameter = Parameter(domain="stat", key="quality", value_number=65)
    constraint = ParameterConstraint(
        domain="stat", key="quality", operator=Operator.GTE, value_number=70
    )

    assert ConstraintMatcher.matches(parameter, constraint) is False


def test_constraint_eq_matches():
    """Test that = operator matches when values are equal."""
    parameter = Parameter(domain="identity", key="name", value_string="iron_ore")
    constraint = ParameterConstraint(
        domain="identity", key="name", operator=Operator.EQ, value_string="iron_ore"
    )

    assert ConstraintMatcher.matches(parameter, constraint) is True


def test_constraint_eq_no_match():
    """Test that = operator doesn't match when values differ."""
    parameter = Parameter(domain="identity", key="name", value_string="iron_ore")
    constraint = ParameterConstraint(
        domain="identity", key="name", operator=Operator.EQ, value_string="copper_ore"
    )

    assert ConstraintMatcher.matches(parameter, constraint) is False


def test_wildcard_domain_matches():
    """Test that wildcard domain matches any domain with the key."""
    parameter = Parameter(domain="classification", key="metal", value_boolean=True)
    constraint = ParameterConstraint(
        domain="*", key="metal", operator=Operator.EXISTS, is_wildcard=True
    )

    assert ConstraintMatcher.matches(parameter, constraint) is True


def test_wildcard_domain_no_match():
    """Test that wildcard domain doesn't match when key differs."""
    parameter = Parameter(domain="classification", key="wood", value_boolean=True)
    constraint = ParameterConstraint(
        domain="*", key="metal", operator=Operator.EXISTS, is_wildcard=True
    )

    assert ConstraintMatcher.matches(parameter, constraint) is False


def test_wildcard_key_matches():
    """Test that wildcard key matches any key with the domain."""
    parameter = Parameter(domain="classification", key="metal", value_boolean=True)
    constraint = ParameterConstraint(
        domain="classification", key="*", operator=Operator.EXISTS, is_wildcard=True
    )

    assert ConstraintMatcher.matches(parameter, constraint) is True


def test_wildcard_key_no_match():
    """Test that wildcard key doesn't match when domain differs."""
    parameter = Parameter(domain="identity", key="metal", value_boolean=True)
    constraint = ParameterConstraint(
        domain="classification", key="*", operator=Operator.EXISTS, is_wildcard=True
    )

    assert ConstraintMatcher.matches(parameter, constraint) is False


def test_constraint_lt_matches():
    """Test that < operator matches when value is less."""
    parameter = Parameter(domain="stat", key="quality", value_number=65)
    constraint = ParameterConstraint(
        domain="stat", key="quality", operator=Operator.LT, value_number=70
    )

    assert ConstraintMatcher.matches(parameter, constraint) is True


def test_constraint_lt_no_match():
    """Test that < operator doesn't match when value is greater."""
    parameter = Parameter(domain="stat", key="quality", value_number=78)
    constraint = ParameterConstraint(
        domain="stat", key="quality", operator=Operator.LT, value_number=70
    )

    assert ConstraintMatcher.matches(parameter, constraint) is False


def test_constraint_lte_matches():
    """Test that <= operator matches when value is less or equal."""
    parameter = Parameter(domain="stat", key="quality", value_number=70)
    constraint = ParameterConstraint(
        domain="stat", key="quality", operator=Operator.LTE, value_number=70
    )

    assert ConstraintMatcher.matches(parameter, constraint) is True


def test_constraint_gt_matches():
    """Test that > operator matches when value is greater."""
    parameter = Parameter(domain="stat", key="quality", value_number=78)
    constraint = ParameterConstraint(
        domain="stat", key="quality", operator=Operator.GT, value_number=70
    )

    assert ConstraintMatcher.matches(parameter, constraint) is True


def test_type_mismatch_no_match():
    """Test that type mismatch doesn't match."""
    parameter = Parameter(domain="stat", key="quality", value_string="78")
    constraint = ParameterConstraint(
        domain="stat", key="quality", operator=Operator.GTE, value_number=70
    )

    assert ConstraintMatcher.matches(parameter, constraint) is False
