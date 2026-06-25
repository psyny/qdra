import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.entity import Entity
from models.entity_parameter import EntityParameter
from models.slot import Slot
from models.project_template import ProjectTemplateSlotGroup
from models.image_asset import ImageAsset
from repositories.entity_repository import EntityRepository
from repositories.entity_parameter_repository import EntityParameterRepository
from repositories.project_repository import ProjectRepository
from repositories.project_template_repository import ProjectTemplateRepository
from repositories.image_asset_repository import ImageAssetRepository
from repositories.slot_repository import SlotRepository
from repositories.option_repository import OptionRepository
from repositories.parameter_constraint_repository import ParameterConstraintRepository
from infrastructure.storage.image_storage_provider import ImageStorageProvider
from infrastructure.storage.local_image_storage_provider import LocalImageStorageProvider
from infrastructure.storage.s3_image_storage_provider import S3ImageStorageProvider
from infrastructure.cache.entity_cache import set_entity_with_data, get_entity_with_data, get_entity_cache, invalidate_entity
from infrastructure.config.settings import settings
from infrastructure.cache.cache_service import CacheService


class EntityService:
    def __init__(self, db: Session):
        self.db = db
        self.entity_repository = EntityRepository(db)
        self.entity_parameter_repository = EntityParameterRepository(db)
        self.project_repository = ProjectRepository(db)
        self.template_repository = ProjectTemplateRepository(db)
        self.image_asset_repository = ImageAssetRepository(db)
        self.slot_repository = SlotRepository(db)
        self.option_repository = OptionRepository(db)
        self.constraint_repository = ParameterConstraintRepository(db)
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
        auto_create_slots: bool = True,
    ) -> Entity:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project '{project_id}' not found")

        entity_type = self.template_repository.get_entity_type_by_id(entity_type_id)
        if not entity_type:
            raise ValueError(f"EntityType '{entity_type_id}' not found")

        entity = self.entity_repository.create(
            project_id=project_id,
            entity_type_id=entity_type_id,
            group=group,
        )

        # TODO: Reimplement auto-create slots from template after new slot system is designed
        # if auto_create_slots and entity_type.kind == "recipe":
        #     self._create_slots_from_template(entity)

        return entity

    async def get_entity(self, entity_id: uuid.UUID) -> Dict[str, Any]:
        from datetime import datetime
        
        # Use a separate cache key for the flat structure (service layer)
        # to avoid conflict with repository's nested structure cache
        cache = get_entity_cache()
        flat_key = f"flat:{entity_id}"
        cached_flat = cache.get(flat_key)
        if cached_flat:
            return cached_flat
        
        # Cache miss: resolve from DB
        entity = self.entity_repository.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        # Get entity_type
        entity_type = self.template_repository.get_entity_type_by_id(entity.entity_type_id)
        kind = entity_type.kind if entity_type else "unknown"

        # Get image
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

        # Get parameters (uses cache)
        parameters = self.get_entity_parameters(entity_id)
        result["parameters"] = [
            {
                "id": str(p.id),
                "entity_id": str(p.entity_id),
                "domain": p.domain,
                "key": p.key,
                "value_string": p.value_string,
                "value_number": p.value_number,
                "value_boolean": p.value_boolean,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            for p in parameters
        ]

        # Get slots for recipe entities
        if kind == "recipe":
            slots = self.slot_repository.list_by_recipe_entity(entity_id)
            result["slots"] = [
                {
                    "id": str(slot.id),
                    "kind": slot.kind,
                    "sort_order": slot.sort_order,
                }
                for slot in slots
            ]

        # Cache the flat structure with separate key
        cache[flat_key] = result

        return result

    async def get_entities(self, entity_ids: List[uuid.UUID]) -> List[Dict[str, Any]]:
        """Get resolved entities by list of IDs (uses cache for resolved data)."""
        result = []
        for entity_id in entity_ids:
            entity_data = await self.get_entity(entity_id)
            result.append(entity_data)
        return result

    async def list_entities(
        self,
        project_id: uuid.UUID,
        kind: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List entities by project (base data only, no resolved data like images/parameters)."""
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project '{project_id}' not found")

        entities = self.entity_repository.list_by_project(project_id, kind=kind)
        
        # Return base entity data with kind (no resolved data like images, parameters)
        result = []
        for entity in entities:
            entity_type = self.template_repository.get_entity_type_by_id(entity.entity_type_id)
            result.append({
                "id": entity.id,
                "project_id": entity.project_id,
                "entity_type_id": entity.entity_type_id,
                "group": entity.group,
                "kind": entity_type.kind if entity_type else "unknown",
                "created_at": entity.created_at,
                "updated_at": entity.updated_at,
            })
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

        # Invalidate cache for this entity
        cache = get_entity_cache()
        entity_id_str = str(entity_id)
        cache.pop(f"flat:{entity_id_str}", None)
        cache.pop(f"params:{entity_id_str}", None)
        invalidate_entity(entity_id)

        return self.entity_parameter_repository.create(
            entity_id=entity_id,
            domain=domain,
            key=key,
            value_string=value_string,
            value_number=value_number,
            value_boolean=value_boolean,
        )

    def delete_parameter(self, parameter_id: uuid.UUID) -> bool:
        # Get the parameter first to find the entity_id
        param = self.entity_parameter_repository.get_by_id(parameter_id)
        if param:
            # Invalidate cache for this entity
            cache = get_entity_cache()
            entity_id_str = str(param.entity_id)
            cache.pop(f"flat:{entity_id_str}", None)
            cache.pop(f"params:{entity_id_str}", None)
            invalidate_entity(param.entity_id)
        
        return self.entity_parameter_repository.delete(parameter_id)

    def get_basic_entity(self, entity_id: uuid.UUID) -> Optional[Entity]:
        """Get the basic Entity object with caching. Returns None if not found."""
        # Try cache first
        cached = get_entity_with_data(entity_id)
        if cached:
            # Reconstruct Entity from cached data
            return Entity(
                id=uuid.UUID(cached["id"]),
                project_id=uuid.UUID(cached["project_id"]),
                entity_type_id=uuid.UUID(cached["entity_type_id"]),
                group=cached["group"],
                created_at=cached["created_at"],
                updated_at=cached["updated_at"],
            )
        
        # Cache miss: query from DB
        return self.entity_repository.get_by_id(entity_id)

    def get_entity_parameters(self, entity_id: uuid.UUID) -> List[EntityParameter]:
        # Use a separate cache key for parameters to avoid conflicts
        cache = get_entity_cache()
        params_key = f"params:{entity_id}"
        cached_params = cache.get(params_key)
        if cached_params:
            return [
                EntityParameter(
                    id=uuid.UUID(p["id"]),
                    entity_id=uuid.UUID(p["entity_id"]),
                    domain=p["domain"],
                    key=p["key"],
                    value_string=p["value_string"],
                    value_number=p["value_number"],
                    value_boolean=p["value_boolean"],
                    created_at=p["created_at"],
                    updated_at=p["updated_at"],
                )
                for p in cached_params
            ]
        
        # Cache miss: query from DB
        params = self.entity_parameter_repository.list_by_entity(entity_id)
        
        # Cache the parameters with datetime fields
        cache[params_key] = [
            {
                "id": str(p.id),
                "entity_id": str(p.entity_id),
                "domain": p.domain,
                "key": p.key,
                "value_string": p.value_string,
                "value_number": p.value_number,
                "value_boolean": p.value_boolean,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            for p in params
        ]
        
        return params

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
        """List entities filtered by a view config's entity_type_id (base data only, no resolved data like images/parameters)."""
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
        # Return base entity data with kind (no resolved data like images, parameters)
        result = []
        for entity in entities:
            entity_type = self.template_repository.get_entity_type_by_id(entity.entity_type_id)
            result.append({
                "id": entity.id,
                "project_id": entity.project_id,
                "entity_type_id": entity.entity_type_id,
                "group": entity.group,
                "kind": entity_type.kind if entity_type else "unknown",
                "created_at": entity.created_at,
                "updated_at": entity.updated_at,
            })
        return result
