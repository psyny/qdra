import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.parameter_constraint import ParameterConstraint, Operator


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
