from typing import Any
from models.parameter import Parameter
from models.parameter_constraint import ParameterConstraint, Operator


class ConstraintMatcher:
    @staticmethod
    def matches(parameter: Parameter, constraint: ParameterConstraint) -> bool:
        """Check if a parameter matches a constraint."""
        # Get parameter value
        param_value = ConstraintMatcher._get_parameter_value(parameter)
        if param_value is None:
            return False

        # Get constraint value
        constraint_value = ConstraintMatcher._get_constraint_value(constraint)

        # Handle wildcard domain/key
        if constraint.is_wildcard:
            if constraint.domain == "*" and constraint.key == "*":
                # Wildcard on both - check if parameter has any value
                return param_value is not None
            elif constraint.domain == "*":
                # Wildcard domain - match any domain with the key
                if parameter.key != constraint.key:
                    return False
                return param_value is not None
            elif constraint.key == "*":
                # Wildcard key - match any key with the domain
                if parameter.domain != constraint.domain:
                    return False
                return param_value is not None

        # Check domain and key match
        if not constraint.is_wildcard:
            if constraint.domain != "*" and parameter.domain != constraint.domain:
                return False
            if constraint.key != "*" and parameter.key != constraint.key:
                return False

        # Handle exists operator
        if constraint.operator == Operator.EXISTS:
            return param_value is not None

        # Handle comparison operators
        if constraint_value is None:
            return False

        # Type checking for comparisons
        if type(param_value) != type(constraint_value):
            return False

        # Apply operator
        if constraint.operator == Operator.EQ:
            return param_value == constraint_value
        elif constraint.operator == Operator.LT:
            return param_value < constraint_value
        elif constraint.operator == Operator.LTE:
            return param_value <= constraint_value
        elif constraint.operator == Operator.GT:
            return param_value > constraint_value
        elif constraint.operator == Operator.GTE:
            return param_value >= constraint_value
        elif constraint.operator == Operator.IN:
            # IN operator expects constraint_value to be a list
            if not isinstance(constraint_value, list):
                return False
            return param_value in constraint_value

        return False

    @staticmethod
    def _get_parameter_value(parameter: Parameter) -> Any:
        """Extract the value from a parameter (exactly one should be set)."""
        if parameter.value_string is not None:
            return parameter.value_string
        elif parameter.value_number is not None:
            return parameter.value_number
        elif parameter.value_boolean is not None:
            return parameter.value_boolean
        return None

    @staticmethod
    def _get_constraint_value(constraint: ParameterConstraint) -> Any:
        """Extract the value from a constraint."""
        if constraint.value_string is not None:
            return constraint.value_string
        elif constraint.value_number is not None:
            return constraint.value_number
        elif constraint.value_boolean is not None:
            return constraint.value_boolean
        return None
