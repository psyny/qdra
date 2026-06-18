import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.entity import Entity
from models.project_template import ProjectTemplateEntityType


class EntityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        project_id: uuid.UUID,
        entity_type_id: uuid.UUID,
    ) -> Entity:
        entity = Entity(
            project_id=project_id,
            entity_type_id=entity_type_id,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, entity_id: uuid.UUID) -> Optional[Entity]:
        return self.db.query(Entity).filter(Entity.id == entity_id).first()

    def list_by_project(
        self, project_id: uuid.UUID, kind: Optional[str] = None
    ) -> List[Entity]:
        q = self.db.query(Entity).filter(Entity.project_id == project_id)
        if kind is not None:
            q = q.join(ProjectTemplateEntityType).filter(ProjectTemplateEntityType.kind == kind)
        return q.all()

    def list_by_entity_type(self, entity_type_id: uuid.UUID) -> List[Entity]:
        return (
            self.db.query(Entity)
            .filter(Entity.entity_type_id == entity_type_id)
            .all()
        )

    def list_by_project_and_entity_type(
        self, project_id: uuid.UUID, entity_type_id: uuid.UUID
    ) -> List[Entity]:
        return (
            self.db.query(Entity)
            .filter(Entity.project_id == project_id)
            .filter(Entity.entity_type_id == entity_type_id)
            .all()
        )

    def delete(self, entity_id: uuid.UUID) -> bool:
        entity = self.get_by_id(entity_id)
        if not entity:
            return False
        self.db.delete(entity)
        self.db.commit()
        return True
