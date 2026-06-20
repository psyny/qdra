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
from infrastructure.storage.image_storage_provider import ImageStorageProvider
from infrastructure.storage.local_image_storage_provider import LocalImageStorageProvider
from infrastructure.storage.s3_image_storage_provider import S3ImageStorageProvider
from infrastructure.config.settings import settings
from qdra.infrastructure.cache.cache_service import CacheService


class EntityService:
    def __init__(self, db: Session):
        self.db = db
        self.entity_repository = EntityRepository(db, CacheService())
        self.entity_parameter_repository = EntityParameterRepository(db)
        self.project_repository = ProjectRepository(db)
        self.template_repository = ProjectTemplateRepository(db)
        self.image_asset_repository = ImageAssetRepository(db)
        self.storage_provider = self._get_storage_provider()
    
    def _get_storage_provider(self) -> ImageStorageProvider:
        """Get the configured storage provider."""
        if settings.image_storage_backend == "local":
            return LocalImageStorageProvider(settings.local_storage_root)
        elif settings.image_storage_backend == "s3":
            return S3ImageStorageProvider(
                bucket=settings.s3_bucket,
                region=settings.s3_region,
                endpoint_url=settings.s3_endpoint_url or None,
                access_key_id=settings.s3_access_key_id or None,
                secret_access_key=settings.s3_secret_access_key or None,
                public_base_url=settings.s3_public_base_url or None,
                force_path_style=getattr(settings, 's3_force_path_style', False),
            )
        else:
            raise ValueError(f"Unknown storage backend: {settings.image_storage_backend}")

    def create_entity(
        self,
        project_id: uuid.UUID,
        entity_type_id: uuid.UUID,
        group: str = "",
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
            group=group,
        )

    async def get_entity(self, entity_id: uuid.UUID) -> Dict[str, Any]:
        from datetime import datetime
        entity = self.entity_repository.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        entity_type = self.template_repository.get_entity_type_by_id(entity.entity_type_id)
        kind = entity_type.kind if entity_type else "unknown"

        image = self.image_asset_repository.get_primary_image(entity.id)

        # Ensure updated_at is set (fallback for test environments)
        updated_at = entity.updated_at or entity.created_at or datetime.utcnow()

        result: Dict[str, Any] = {
            "id": entity.id,
            "project_id": entity.project_id,
            "entity_type_id": entity.entity_type_id,
            "group": entity.group,
            "kind": kind,
            "created_at": entity.created_at,
            "updated_at": updated_at,
            "image": None,
        }

        if image and image.status == 'ready':
            # Generate presigned download URL
            download_url = await self.storage_provider.create_presigned_download_url(
                storage_key=image.storage_key,
                expires_in_seconds=3600,
            )
            result["image"] = {
                "id": image.id,
                "url": download_url,
                "mime_type": image.mime_type,
                "alt_text": image.alt_text,
                "width": image.width,
                "height": image.height,
            }

        return result

    async def list_entities(
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
                "group": entity.group,
                "kind": entity_kind,
                "created_at": entity.created_at,
                "updated_at": entity.updated_at,
                "image": None,
            }
            if image and image.status == 'ready':
                # Generate presigned download URL
                download_url = await self.storage_provider.create_presigned_download_url(
                    storage_key=image.storage_key,
                    expires_in_seconds=3600,
                )
                entity_data["image"] = {
                    "id": image.id,
                    "url": download_url,
                    "mime_type": image.mime_type,
                    "alt_text": image.alt_text,
                    "width": image.width,
                    "height": image.height,
                }
            result.append(entity_data)

        return result

    def delete_entity(self, entity_id: uuid.UUID) -> bool:
        entity = self.entity_repository.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")
        
        # Delete images from storage before deleting the entity
        images = self.image_asset_repository.get_by_entity_id(entity_id)
        for image in images:
            try:
                self.storage_provider.delete(image.storage_key)
            except Exception:
                pass  # Ignore storage deletion errors
        
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

    def get_distinct_parameter_values(
        self,
        entity_type_id: uuid.UUID,
        group: str,
        domain: str,
        key: str,
    ) -> List[str]:
        """Get all distinct string values for a given entity type, group, domain, and key."""
        entity_type = self.template_repository.get_entity_type_by_id(entity_type_id)
        if not entity_type:
            raise ValueError(f"EntityType '{entity_type_id}' not found")

        result = self.entity_parameter_repository.list_distinct_values_by_entity_type_domain_key(
            entity_type_id, group, domain, key
        )
        return [row[0] for row in result]

    async def list_entities_by_view_config(
        self,
        project_id: uuid.UUID,
        view_config_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """List entities filtered by a view config's entity_type_id and filter_params."""
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project '{project_id}' not found")

        view_config = self.template_repository.get_view_config_by_id(view_config_id)
        if not view_config:
            raise ValueError(f"View config '{view_config_id}' not found")

        entity_type_id = view_config.entity_type_id
        if not entity_type_id:
            raise ValueError(f"View config '{view_config_id}' has no entity_type_id")

        # Get entities by project and entity type
        entities = self.entity_repository.list_by_project_and_entity_type(
            project_id, entity_type_id
        )

        # TODO: Apply filter_params from view_config if needed
        # For now, return all entities of the type
        result = []

        for entity in entities:
            entity_type = self.template_repository.get_entity_type_by_id(entity.entity_type_id)
            entity_kind = entity_type.kind if entity_type else "unknown"

            image = self.image_asset_repository.get_primary_image(entity.id)
            entity_data: Dict[str, Any] = {
                "id": entity.id,
                "project_id": entity.project_id,
                "entity_type_id": entity.entity_type_id,
                "group": entity.group,
                "kind": entity_kind,
                "created_at": entity.created_at,
                "updated_at": entity.updated_at,
                "image": None,
            }
            if image and image.status == 'ready':
                # Generate presigned download URL
                download_url = await self.storage_provider.create_presigned_download_url(
                    storage_key=image.storage_key,
                    expires_in_seconds=3600,
                )
                entity_data["image"] = {
                    "id": image.id,
                    "url": download_url,
                    "mime_type": image.mime_type,
                    "alt_text": image.alt_text,
                    "width": image.width,
                    "height": image.height,
                }
            result.append(entity_data)

        return result
