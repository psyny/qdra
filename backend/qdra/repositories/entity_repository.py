import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from models.entity import Entity
from models.project_template import ProjectTemplateEntityType
from infrastructure.cache.entity_cache import get_entity_with_data, set_entity_with_data, invalidate_entity
from infrastructure.config.settings import settings


class EntityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        project_id: uuid.UUID,
        entity_type_id: uuid.UUID,
        group: str = "",
    ) -> Entity:
        from datetime import datetime
        entity = Entity(
            project_id=project_id,
            entity_type_id=entity_type_id,
            group=group,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        # Ensure updated_at is set (in case server_default didn't work)
        if entity.updated_at is None:
            entity.updated_at = entity.created_at or datetime.utcnow()
            self.db.commit()
        return entity

    def get_by_id(self, entity_id: uuid.UUID) -> Optional[Entity]:
        from datetime import datetime
        
        # Try cache first
        cached = get_entity_with_data(entity_id)
        if cached:
            entity_data = cached.get("entity")
            if entity_data:
                entity = self._deserialize_entity(entity_data)
                if entity:
                    return entity
        
        # Query database
        entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
        if entity:
            # Ensure updated_at is set (fallback for test environments)
            if entity.updated_at is None:
                entity.updated_at = entity.created_at or datetime.utcnow()
                self.db.commit()
            # Cache the entity (without parameters/slots for now)
            data = {
                "entity": self._serialize_entity(entity),
                "parameters": [],
                "slots": [],
            }
            set_entity_with_data(entity_id, data)
        
        return entity
    
    
    def _serialize_entity(self, entity: Entity) -> dict:
        """Serialize entity for Redis storage."""
        return {
            "id": str(entity.id),
            "project_id": str(entity.project_id),
            "entity_type_id": str(entity.entity_type_id),
            "group": entity.group,
            "created_at": entity.created_at.isoformat() if entity.created_at else None,
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
        }
    
    def _deserialize_entity(self, data: dict) -> Optional[Entity]:
        """Deserialize entity from Redis storage."""
        try:
            return Entity(
                id=uuid.UUID(data["id"]),
                project_id=uuid.UUID(data["project_id"]),
                entity_type_id=uuid.UUID(data["entity_type_id"]),
                group=data.get("group", ""),
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
            )
        except Exception:
            return None
    
    def invalidate_entity(self, entity_id: uuid.UUID) -> None:
        """Invalidate entity from cache."""
        invalidate_entity(entity_id)

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
        # Query directly from database to ensure entity is attached to session
        entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            return False
        self.invalidate_entity(entity_id)
        self.db.delete(entity)
        self.db.commit()
        return True
