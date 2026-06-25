import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from models.entity import Entity
from models.project_template import ProjectTemplateEntityType
from models.image_asset import ImageAsset
from models.entity_parameter import EntityParameter
from infrastructure.cache.entity_cache import get_entity_with_data, set_entity_with_data
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
            
            # Fetch entity_type and image for caching
            entity_type = self.db.query(ProjectTemplateEntityType).filter(
                ProjectTemplateEntityType.id == entity.entity_type_id
            ).first()
            
            image = self.db.query(ImageAsset).filter(
                ImageAsset.entity_id == entity_id,
                ImageAsset.status == 'ready'
            ).first()
            
            # Fetch parameters for caching
            parameters = self.db.query(EntityParameter).filter(
                EntityParameter.entity_id == entity_id
            ).all()
            
            # Cache the entity with entity_type, image, and parameters
            data = {
                "entity": self._serialize_entity(entity),
                "entity_type": self._serialize_entity_type(entity_type) if entity_type else None,
                "image": self._serialize_image(image) if image else None,
                "parameters": self._serialize_parameters(parameters),
                "slots": [],
            }
            set_entity_with_data(entity_id, data)
        
        return entity
    
    def get_entity_with_cached_data(self, entity_id: uuid.UUID) -> tuple[Optional[Entity], Optional[dict]]:
        """Get entity and its cached data (entity_type, image) together."""
        from datetime import datetime
        
        # Try cache first
        cached = get_entity_with_data(entity_id)
        if cached:
            entity_data = cached.get("entity")
            if entity_data:
                entity = self._deserialize_entity(entity_data)
                if entity:
                    return entity, cached
        
        # Query database and cache
        entity = self.get_by_id(entity_id)
        if entity:
            cached = get_entity_with_data(entity_id)
            return entity, cached
        
        return None, None
    
    
    def _serialize_entity_type(self, entity_type: ProjectTemplateEntityType) -> dict:
        """Serialize entity_type for cache storage."""
        return {
            "id": str(entity_type.id),
            "name": entity_type.name,
            "kind": entity_type.kind,
        }
    
    def _serialize_image(self, image: ImageAsset) -> dict:
        """Serialize image for cache storage."""
        return {
            "id": str(image.id),
            "storage_key": image.storage_key,
            "mime_type": image.mime_type,
            "width": image.width,
            "height": image.height,
            "alt_text": image.alt_text,
        }
    
    def _serialize_parameters(self, parameters: List[EntityParameter]) -> List[dict]:
        """Serialize parameters for cache storage."""
        return [
            {
                "id": str(p.id),
                "entity_id": str(p.entity_id),
                "domain": p.domain,
                "key": p.key,
                "value_string": p.value_string,
                "value_number": p.value_number,
                "value_boolean": p.value_boolean,
            }
            for p in parameters
        ]
    
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
        self.db.delete(entity)
        self.db.commit()
        return True
