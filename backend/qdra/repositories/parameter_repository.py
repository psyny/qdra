import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.parameter import Parameter


class ParameterRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        material_id: uuid.UUID,
        domain: str,
        key: str,
        value_string: Optional[str] = None,
        value_number: Optional[float] = None,
        value_boolean: Optional[bool] = None,
    ) -> Parameter:
        parameter = Parameter(
            material_id=material_id,
            domain=domain,
            key=key,
            value_string=value_string,
            value_number=value_number,
            value_boolean=value_boolean,
        )
        self.db.add(parameter)
        self.db.commit()
        self.db.refresh(parameter)
        return parameter

    def get_by_id(self, parameter_id: uuid.UUID) -> Optional[Parameter]:
        return self.db.query(Parameter).filter(Parameter.id == parameter_id).first()

    def delete(self, parameter_id: uuid.UUID) -> bool:
        parameter = self.get_by_id(parameter_id)
        if parameter:
            self.db.delete(parameter)
            self.db.commit()
            return True
        return False

    def list_by_material(self, material_id: uuid.UUID) -> List[Parameter]:
        return self.db.query(Parameter).filter(Parameter.material_id == material_id).all()
