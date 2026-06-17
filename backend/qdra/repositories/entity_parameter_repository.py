import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.entity_parameter import EntityParameter


class EntityParameterRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        entity_id: uuid.UUID,
        domain: str,
        key: str,
        value_string: Optional[str] = None,
        value_number: Optional[float] = None,
        value_boolean: Optional[bool] = None,
    ) -> EntityParameter:
        parameter = EntityParameter(
            entity_id=entity_id,
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

    def get_by_id(self, parameter_id: uuid.UUID) -> Optional[EntityParameter]:
        return (
            self.db.query(EntityParameter)
            .filter(EntityParameter.id == parameter_id)
            .first()
        )

    def list_by_entity(self, entity_id: uuid.UUID) -> List[EntityParameter]:
        return (
            self.db.query(EntityParameter)
            .filter(EntityParameter.entity_id == entity_id)
            .all()
        )

    def delete(self, parameter_id: uuid.UUID) -> bool:
        parameter = self.get_by_id(parameter_id)
        if not parameter:
            return False
        self.db.delete(parameter)
        self.db.commit()
        return True
