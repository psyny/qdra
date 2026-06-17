import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.entity import Entity
from models.entity_parameter import EntityParameter
from repositories.entity_repository import EntityRepository
from repositories.entity_parameter_repository import EntityParameterRepository
from repositories.project_repository import ProjectRepository
from repositories.project_template_repository import ProjectTemplateRepository
from repositories.image_asset_repository import ImageAssetRepository


class EntityService:
    def __init__(self, db: Session):
        self.db = db
        self.entity_repository = EntityRepository(db)
        self.entity_parameter_repository = EntityParameterRepository(db)
        self.project_repository = ProjectRepository(db)
        self.template_repository = ProjectTemplateRepository(db)
        self.image_asset_repository = ImageAssetRepository(db)

    def create_entity(
        self,
        project_id: uuid.UUID,
        entity_type_id: uuid.UUID,
    ) -> Entity:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project '{project_id}' not found")

        entity_type = self.template_repository.get_entity_type_by_id(entity_type_id)
        if not entity_type:
            raise ValueError(f"EntityType '{entity_type_id}' not found")

        return self.entity_repository.create(
            project_id=project_id,
            entity_type_id=entity_type_id,
        )

    def get_entity(self, entity_id: uuid.UUID) -> Dict[str, Any]:
        entity = self.entity_repository.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        entity_type = self.template_repository.get_entity_type_by_id(entity.entity_type_id)
        kind = entity_type.kind if entity_type else "unknown"

        image = self.image_asset_repository.get_primary_image(entity.id)

        result: Dict[str, Any] = {
            "id": entity.id,
            "project_id": entity.project_id,
            "entity_type_id": entity.entity_type_id,
            "kind": kind,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "image": None,
        }

        if image:
            result["image"] = {
                "id": image.id,
                "url": f"/projects/{entity.project_id}/images/{image.id}",
                "mime_type": image.mime_type,
                "alt_text": image.alt_text,
            }

        return result

    def list_entities(
        self,
        project_id: uuid.UUID,
        kind: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project '{project_id}' not found")

        entities = self.entity_repository.list_by_project(project_id, kind=kind)
        result = []

        for entity in entities:
            entity_type = self.template_repository.get_entity_type_by_id(entity.entity_type_id)
            entity_kind = entity_type.kind if entity_type else "unknown"

            image = self.image_asset_repository.get_primary_image(entity.id)
            entity_data: Dict[str, Any] = {
                "id": entity.id,
                "project_id": entity.project_id,
                "entity_type_id": entity.entity_type_id,
                "kind": entity_kind,
                "created_at": entity.created_at,
                "updated_at": entity.updated_at,
                "image": None,
            }
            if image:
                entity_data["image"] = {
                    "id": image.id,
                    "url": f"/projects/{entity.project_id}/images/{image.id}",
                    "mime_type": image.mime_type,
                    "alt_text": image.alt_text,
                }
            result.append(entity_data)

        return result

    def delete_entity(self, entity_id: uuid.UUID) -> bool:
        entity = self.entity_repository.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")
        return self.entity_repository.delete(entity_id)

    def add_parameter(
        self,
        entity_id: uuid.UUID,
        domain: str,
        key: str,
        value_string: Optional[str] = None,
        value_number: Optional[float] = None,
        value_boolean: Optional[bool] = None,
    ) -> EntityParameter:
        entity = self.entity_repository.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        values_provided = sum(
            [
                value_string is not None,
                value_number is not None,
                value_boolean is not None,
            ]
        )
        if values_provided != 1:
            raise ValueError("Exactly one value must be provided")

        return self.entity_parameter_repository.create(
            entity_id=entity_id,
            domain=domain,
            key=key,
            value_string=value_string,
            value_number=value_number,
            value_boolean=value_boolean,
        )

    def delete_parameter(self, parameter_id: uuid.UUID) -> bool:
        return self.entity_parameter_repository.delete(parameter_id)

    def get_entity_parameters(self, entity_id: uuid.UUID) -> List[EntityParameter]:
        entity = self.entity_repository.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")
        return self.entity_parameter_repository.list_by_entity(entity_id)
