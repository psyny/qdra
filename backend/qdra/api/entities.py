import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from services.entity_service import EntityService
from infrastructure.security.permission_checker import (
    require_can_create_material,
    require_can_edit_material,
    require_can_delete_material,
    get_current_user_id,
)
from repositories.project_template_repository import ProjectTemplateRepository
from repositories.project_repository import ProjectRepository

router = APIRouter(prefix="/api")


def _is_material_entity_type(project_id: uuid.UUID, entity_type_id: uuid.UUID, db: Session) -> bool:
    """Check if an entity type is a material kind."""
    project = ProjectRepository(db).get_by_id(project_id)
    if not project:
        return False
    entity_types = ProjectTemplateRepository(db).list_entity_types(
        project.project_template_id, kind="material"
    )
    return any(et.id == entity_type_id for et in entity_types)


def _is_material_entity(entity_id: uuid.UUID, db: Session) -> bool:
    """Check if an existing entity is a material kind."""
    from repositories.entity_repository import EntityRepository
    entity_repo = EntityRepository(db)
    entity = entity_repo.get_by_id(entity_id)
    if not entity:
        return False
    return _is_material_entity_type(entity.project_id, entity.entity_type_id, db)


def _check_material_permission(
    project_id: uuid.UUID,
    permission_name: str,
    db: Session,
    user_id: uuid.UUID
) -> None:
    """Check if user has a specific material permission for the project."""
    from services.user_service import UserService

    user_service = UserService(db)
    permissions = user_service.get_project_permissions(user_id, project_id)

    if not permissions:
        raise HTTPException(status_code=403, detail="You do not have access to this project")

    if not getattr(permissions, permission_name, False):
        raise HTTPException(
            status_code=403,
            detail=f"Permission '{permission_name}' is required"
        )


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ParameterValueModel(BaseModel):
    domain: str
    key: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None


class GroupsRequest(BaseModel):
    groups: List[str] = []


class ParameterValuesRequest(BaseModel):
    domain: str
    key: str
    groups: List[str] = []


class CreateEntityRequest(BaseModel):
    entity_type_id: uuid.UUID
    group: str = ""
    parameters: Optional[List[ParameterValueModel]] = None


class BulkCreateEntityRequest(BaseModel):
    entities: List[CreateEntityRequest]


class EntityParameterResponse(BaseModel):
    id: uuid.UUID
    entity_id: uuid.UUID
    domain: str
    key: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EntityResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    entity_type_id: uuid.UUID
    group: str
    kind: str
    created_at: datetime
    updated_at: datetime
    image: Optional[Dict[str, Any]] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    slots: Optional[List[Dict[str, Any]]] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/projects/{project_id}/entities", response_model=EntityResponse)
async def create_entity(
    project_id: uuid.UUID,
    request: CreateEntityRequest,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    from qdra.infrastructure.cache.invalidation_controller import entities_added

    # Check if this is a material entity type
    is_material = _is_material_entity_type(project_id, request.entity_type_id, db)

    # If it's a material, check create permission
    if is_material:
        _check_material_permission(project_id, "can_create_material", db, user_id)

    service = EntityService(db)
    try:
        entity = service.create_entity(
            project_id=project_id,
            entity_type_id=request.entity_type_id,
            group=request.group,
        )
        if request.parameters:
            for param in request.parameters:
                service.add_parameter(
                    entity_id=entity.id,
                    domain=param.domain,
                    key=param.key,
                    value_string=param.value_string,
                    value_number=param.value_number,
                    value_boolean=param.value_boolean,
                )
        # Invalidate all relationship caches so the solver sees the new entity
        entities_added([entity.id], project_id)
        return await service.get_entity(entity.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/entities/bulk", response_model=List[EntityResponse])
async def bulk_create_entities(
    project_id: uuid.UUID,
    request: BulkCreateEntityRequest,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    from qdra.infrastructure.cache.invalidation_controller import entities_added

    service = EntityService(db)
    results = []
    try:
        for item in request.entities:
            # Check if this is a material entity type
            is_material = _is_material_entity_type(project_id, item.entity_type_id, db)

            # If it's a material, check create permission
            if is_material:
                _check_material_permission(project_id, "can_create_material", db, user_id)

            entity = service.create_entity(
                project_id=project_id,
                entity_type_id=item.entity_type_id,
                group=item.group,
            )
            if item.parameters:
                for param in item.parameters:
                    service.add_parameter(
                        entity_id=entity.id,
                        domain=param.domain,
                        key=param.key,
                        value_string=param.value_string,
                        value_number=param.value_number,
                        value_boolean=param.value_boolean,
                    )
            results.append(await service.get_entity(entity.id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    # Invalidate all relationship caches so the solver sees the new entities
    entities_added([e.id for e in results], project_id)
    return results


@router.get("/projects/{project_id}/entities", response_model=List[EntityResponse])
async def list_entities(
    project_id: uuid.UUID,
    kind: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List entities by project (base data only)."""
    service = EntityService(db)
    try:
        return await service.list_entities(project_id=project_id, kind=kind)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


class EntityIdsRequest(BaseModel):
    entity_ids: List[uuid.UUID]

@router.post("/entities/resolved", response_model=List[EntityResponse])
async def get_entities_resolved(
    request: EntityIdsRequest,
    db: Session = Depends(get_db),
):
    """Get resolved entities by list of IDs (includes images, parameters, etc.)."""
    service = EntityService(db)
    try:
        return await service.get_entities(request.entity_ids)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/projects/{project_id}/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    project_id: uuid.UUID,
    entity_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = EntityService(db)
    try:
        return await service.get_entity(entity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


class UpdateEntityRequest(BaseModel):
    parameters: Optional[List[ParameterValueModel]] = None


@router.put("/projects/{project_id}/entities/{entity_id}", response_model=EntityResponse)
async def update_entity(
    project_id: uuid.UUID,
    entity_id: uuid.UUID,
    request: UpdateEntityRequest,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Update an entity's parameters."""
    from qdra.infrastructure.cache.invalidation_controller import entities_changed

    # Check if this is a material entity
    is_material = _is_material_entity(entity_id, db)

    # If it's a material, check edit permission
    if is_material:
        _check_material_permission(project_id, "can_edit_material", db, user_id)

    service = EntityService(db)

    try:
        # Verify entity exists
        await service.get_entity(entity_id)

        # Update parameters if provided
        if request.parameters:
            # First, delete existing parameters for this entity
            existing_params = service.get_entity_parameters(entity_id)
            for param in existing_params:
                service.delete_parameter(param.id)

            # Add new parameters
            for param in request.parameters:
                service.add_parameter(
                    entity_id=entity_id,
                    domain=param.domain,
                    key=param.key,
                    value_string=param.value_string,
                    value_number=param.value_number,
                    value_boolean=param.value_boolean,
                )

            # Invalidate all relationship caches for this project
            entities_changed([entity_id], project_id)

        return await service.get_entity(entity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/projects/{project_id}/entities/{entity_id}", status_code=204)
def delete_entity(
    project_id: uuid.UUID,
    entity_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    from qdra.infrastructure.cache.invalidation_controller import entities_changed

    # Check if this is a material entity
    is_material = _is_material_entity(entity_id, db)

    # If it's a material, check delete permission
    if is_material:
        _check_material_permission(project_id, "can_delete_material", db, user_id)

    service = EntityService(db)
    try:
        service.delete_entity(entity_id)
        # Invalidate all relationship caches for this project
        entities_changed([entity_id], project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/projects/{project_id}/entities/{entity_id}/parameters",
    response_model=EntityParameterResponse,
)
def add_entity_parameter(
    project_id: uuid.UUID,
    entity_id: uuid.UUID,
    request: ParameterValueModel,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    from qdra.infrastructure.cache.invalidation_controller import entities_changed

    # Check if this is a material entity
    is_material = _is_material_entity(entity_id, db)

    # If it's a material, check edit permission
    if is_material:
        _check_material_permission(project_id, "can_edit_material", db, user_id)

    service = EntityService(db)
    try:
        result = service.add_parameter(
            entity_id=entity_id,
            domain=request.domain,
            key=request.key,
            value_string=request.value_string,
            value_number=request.value_number,
            value_boolean=request.value_boolean,
        )
        # Invalidate all relationship caches so constraint lookups reflect the new parameter
        entities_changed([entity_id], project_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/projects/{project_id}/entities/{entity_id}/parameters",
    response_model=List[EntityParameterResponse],
)
def list_entity_parameters(
    project_id: uuid.UUID,
    entity_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = EntityService(db)
    try:
        return service.get_entity_parameters(entity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/projects/{project_id}/view-configs/{config_id}/entities",
    response_model=List[EntityResponse],
)
async def list_entities_by_view_config(
    project_id: uuid.UUID,
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """List entities filtered by a view config's entity_type_id (base data only)."""
    service = EntityService(db)
    try:
        return await service.list_entities_by_view_config(project_id, config_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/projects/{project_id}/entities/{entity_id}/parameters/{parameter_id}",
    status_code=204,
)
def delete_entity_parameter(
    project_id: uuid.UUID,
    entity_id: uuid.UUID,
    parameter_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    from qdra.infrastructure.cache.invalidation_controller import entities_changed

    # Check if this is a material entity
    is_material = _is_material_entity(entity_id, db)

    # If it's a material, check edit permission
    if is_material:
        _check_material_permission(project_id, "can_edit_material", db, user_id)

    service = EntityService(db)
    deleted = service.delete_parameter(parameter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Parameter not found")
    # Invalidate all relationship caches so constraint lookups reflect the removed parameter
    entities_changed([entity_id], project_id)


@router.post("/projects/{project_id}/parameter-values")
def get_values_for_parameter(
    project_id: uuid.UUID,
    request: ParameterValuesRequest,
    db: Session = Depends(get_db),
):
    """Get distinct values for a specific domain:key pair, optionally filtered by groups."""
    from qdra.infrastructure.config.settings import settings
    from qdra.infrastructure.cache.relationship_cache import get_cached_data, set_cached_data
    from services.constraint_resolution_service import ConstraintResolutionService
    from domain.constraints import ConstraintSpec

    domain = request.domain
    key = request.key
    groups = request.groups

    # Check cache first
    cache_key = f"param_values:{project_id}:{domain}:{key}:{','.join(sorted(groups))}"
    if settings.l1_caching:
        cached = get_cached_data(cache_key)
        if cached is not None:
            return cached

    service = EntityService(db)
    constraint_service = ConstraintResolutionService(db)

    try:
        # Build constraints from groups (system.group constraints)
        constraints = []
        if groups:
            for group in groups:
                constraints.append(ConstraintSpec(
                    domain="__system__",
                    key="group",
                    operator="=",
                    value_string=group
                ))

        # Find materials matching the group constraints
        material_ids = constraint_service.find_materials_by_constraints(constraints, project_id)

        # Find recipes matching the group constraints
        recipe_ids = constraint_service.find_recipes_by_constraints(constraints, project_id)

        # Get parameter values for the specified domain:key from these materials and recipes
        all_values = set()
        for material_id in material_ids:
            params = service.get_entity_parameters(material_id)
            for param in params:
                # Check if this parameter matches the domain:key
                if param.domain == domain and param.key == key:
                    if param.value_string is not None:
                        all_values.add(param.value_string)
                    elif param.value_number is not None:
                        all_values.add(str(param.value_number))
                    elif param.value_boolean is not None:
                        all_values.add(str(param.value_boolean))

        for recipe_id in recipe_ids:
            params = service.get_entity_parameters(recipe_id)
            for param in params:
                # Check if this parameter matches the domain:key
                if param.domain == domain and param.key == key:
                    if param.value_string is not None:
                        all_values.add(param.value_string)
                    elif param.value_number is not None:
                        all_values.add(str(param.value_number))
                    elif param.value_boolean is not None:
                        all_values.add(str(param.value_boolean))

        result = sorted(list(all_values))

        # Cache the result
        if settings.l1_caching:
            set_cached_data(cache_key, result)

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
