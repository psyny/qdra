import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from services.entity_service import EntityService

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ParameterValueModel(BaseModel):
    domain: str
    key: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None


class CreateEntityRequest(BaseModel):
    entity_type_id: uuid.UUID
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
    kind: str
    created_at: datetime
    updated_at: datetime
    image: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/projects/{project_id}/entities", response_model=EntityResponse)
async def create_entity(
    project_id: uuid.UUID,
    request: CreateEntityRequest,
    db: Session = Depends(get_db),
):
    service = EntityService(db)
    try:
        entity = service.create_entity(
            project_id=project_id,
            entity_type_id=request.entity_type_id,
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
        return await service.get_entity(entity.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/entities/bulk", response_model=List[EntityResponse])
async def bulk_create_entities(
    project_id: uuid.UUID,
    request: BulkCreateEntityRequest,
    db: Session = Depends(get_db),
):
    service = EntityService(db)
    results = []
    try:
        for item in request.entities:
            entity = service.create_entity(
                project_id=project_id,
                entity_type_id=item.entity_type_id,
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
    return results


@router.get("/projects/{project_id}/entities", response_model=List[EntityResponse])
async def list_entities(
    project_id: uuid.UUID,
    kind: Optional[str] = None,
    db: Session = Depends(get_db),
):
    service = EntityService(db)
    try:
        return await service.list_entities(project_id=project_id, kind=kind)
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
):
    """Update an entity's parameters."""
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
        
        return await service.get_entity(entity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/projects/{project_id}/entities/{entity_id}", status_code=204)
def delete_entity(
    project_id: uuid.UUID,
    entity_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = EntityService(db)
    try:
        service.delete_entity(entity_id)
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
):
    service = EntityService(db)
    try:
        return service.add_parameter(
            entity_id=entity_id,
            domain=request.domain,
            key=request.key,
            value_string=request.value_string,
            value_number=request.value_number,
            value_boolean=request.value_boolean,
        )
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
    """List entities filtered by a view config's entity_type_id and filter_params."""
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
):
    service = EntityService(db)
    deleted = service.delete_parameter(parameter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Parameter not found")
