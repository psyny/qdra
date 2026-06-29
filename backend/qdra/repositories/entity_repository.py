import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from models.entity import Entity
from models.project_template import ProjectTemplateEntityType
from models.image_asset import ImageAsset
from models.entity_parameter import EntityParameter
from infrastructure.cache.entity_cache import get_entity_base, set_entity_base
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

        # Try cache first (flat structure: entity + kind + image metadata)
        cached = get_entity_base(entity_id)
        if cached:
            return self._deserialize_entity(cached)

        # Query database
        entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
        if entity:
            # Ensure updated_at is set (fallback for test environments)
            if entity.updated_at is None:
                entity.updated_at = entity.created_at or datetime.utcnow()
                self.db.commit()

            # Fetch entity_type and image metadata for caching
            entity_type = self.db.query(ProjectTemplateEntityType).filter(
                ProjectTemplateEntityType.id == entity.entity_type_id
            ).first()

            image = self.db.query(ImageAsset).filter(
                ImageAsset.entity_id == entity_id,
                ImageAsset.status == 'ready'
            ).first()

            # Cache the base entity with kind and image metadata (no parameters, no slots)
            data = {
                "id": str(entity.id),
                "project_id": str(entity.project_id),
                "entity_type_id": str(entity.entity_type_id),
                "group": entity.group,
                "kind": entity_type.kind if entity_type else "unknown",
                "created_at": entity.created_at.isoformat() if entity.created_at else None,
                "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
                "image": self._serialize_image(image) if image else None,
            }
            set_entity_base(entity_id, data)

        return entity

    def _serialize_image(self, image: ImageAsset) -> dict:
        """Serialize image metadata for cache storage (no URL)."""
        return {
            "id": str(image.id),
            "storage_key": image.storage_key,
            "mime_type": image.mime_type,
            "width": image.width,
            "height": image.height,
            "alt_text": image.alt_text,
        }

    def _deserialize_entity(self, data: dict) -> Optional[Entity]:
        """Deserialize entity from cache storage (flat structure)."""
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
