import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.parameter_constraint import ParameterConstraint, Operator
from domain.constraints import ConstraintSpec


class ParameterConstraintRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        option_id: uuid.UUID,
        domain: str,
        key: str,
        operator: Operator,
        value_string: Optional[str] = None,
        value_number: Optional[float] = None,
        value_boolean: Optional[bool] = None,
        is_wildcard: bool = False,
    ) -> ParameterConstraint:
        constraint = ParameterConstraint(
            option_id=option_id,
            domain=domain,
            key=key,
            operator=operator,
            value_string=value_string,
            value_number=value_number,
            value_boolean=value_boolean,
            is_wildcard=is_wildcard,
        )
        self.db.add(constraint)
        self.db.commit()
        self.db.refresh(constraint)
        return constraint

    def get_by_id(self, constraint_id: uuid.UUID) -> Optional[ParameterConstraint]:
        return (
            self.db.query(ParameterConstraint)
            .filter(ParameterConstraint.id == constraint_id)
            .first()
        )

    def list_by_option(self, option_id: uuid.UUID) -> List[ParameterConstraint]:
        return (
            self.db.query(ParameterConstraint)
            .filter(ParameterConstraint.option_id == option_id)
            .all()
        )

    def list_by_option_as_specs(self, option_id: uuid.UUID) -> List[ConstraintSpec]:
        """Return constraints as ConstraintSpec domain models."""
        constraints = self.list_by_option(option_id)
        return [self._to_spec(c) for c in constraints]

    def _to_spec(self, model: ParameterConstraint) -> ConstraintSpec:
        """Convert database model to domain ConstraintSpec."""
        return ConstraintSpec(
            domain=model.domain,
            key=model.key,
            operator=model.operator.value if isinstance(model.operator, Operator) else model.operator,
            value_string=model.value_string,
            value_number=model.value_number,
            value_boolean=model.value_boolean,
            is_wildcard=model.is_wildcard,
        )

    def _from_spec(self, spec: ConstraintSpec, option_id: uuid.UUID) -> ParameterConstraint:
        """Convert domain ConstraintSpec to database model."""
        # Convert string operator to Enum if needed
        operator_enum = Operator(spec.operator) if isinstance(spec.operator, str) else spec.operator
        
        return ParameterConstraint(
            option_id=option_id,
            domain=spec.domain,
            key=spec.key,
            operator=operator_enum,
            value_string=spec.value_string,
            value_number=spec.value_number,
            value_boolean=spec.value_boolean,
            is_wildcard=spec.is_wildcard,
        )
