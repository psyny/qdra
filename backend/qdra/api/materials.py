"""Compatibility wrapper: materials are entities with kind='material'."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from services.entity_service import EntityService
from repositories.project_template_repository import ProjectTemplateRepository
from repositories.project_repository import ProjectRepository

router = APIRouter()


def _resolve_entity_type_id(
    project_id: uuid.UUID,
    entity_type_id: Optional[uuid.UUID],
    db: Session,
) -> uuid.UUID:
    if entity_type_id:
        return entity_type_id
    project = ProjectRepository(db).get_by_id(project_id)
    if not project:
        raise ValueError(f"Project '{project_id}' not found")
    types = ProjectTemplateRepository(db).list_entity_types(
        project.project_template_id, kind="material"
    )
    if not types:
        raise ValueError("No material entity types defined in the project template")
    return types[0].id


class MaterialResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    entity_type_id: uuid.UUID
    kind: str
    created_at: datetime
    updated_at: datetime
    image: Optional[Dict[str, Any]] = None


class ParameterCreate(BaseModel):
    domain: str
    key: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None


class MaterialCreate(BaseModel):
    entity_type_id: Optional[uuid.UUID] = None
    parameters: Optional[List[ParameterCreate]] = None


class MaterialBulkCreate(BaseModel):
    materials: Optional[List[MaterialCreate]] = None
    parameters: Optional[List[ParameterCreate]] = None


class ParameterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    entity_id: uuid.UUID
    domain: str
    key: str
    value_string: Optional[str]
    value_number: Optional[float]
    value_boolean: Optional[bool]
    created_at: datetime
    updated_at: datetime


@router.post("/projects/{project_id}/materials", response_model=MaterialResponse, status_code=201)
def create_material(
    project_id: uuid.UUID,
    data: MaterialCreate,
    db: Session = Depends(get_db),
):
    service = EntityService(db)
    try:
        et_id = _resolve_entity_type_id(project_id, data.entity_type_id, db)
        entity = service.create_entity(project_id=project_id, entity_type_id=et_id)
        if data.parameters:
            for p in data.parameters:
                service.add_parameter(
                    entity_id=entity.id, domain=p.domain, key=p.key,
                    value_string=p.value_string, value_number=p.value_number,
                    value_boolean=p.value_boolean,
                )
        return service.get_entity(entity.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/materials/bulk", response_model=MaterialResponse, status_code=201)
def create_material_bulk(
    project_id: uuid.UUID,
    material_data: MaterialBulkCreate,
    db: Session = Depends(get_db),
):
    service = EntityService(db)
    try:
        mat = MaterialCreate(parameters=material_data.parameters)
        if material_data.materials and len(material_data.materials) == 1:
            mat = material_data.materials[0]
        et_id = _resolve_entity_type_id(project_id, mat.entity_type_id, db)
        entity = service.create_entity(project_id=project_id, entity_type_id=et_id)
        for p in (mat.parameters or []):
            service.add_parameter(
                entity_id=entity.id, domain=p.domain, key=p.key,
                value_string=p.value_string, value_number=p.value_number,
                value_boolean=p.value_boolean,
            )
        return service.get_entity(entity.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/materials", response_model=List[MaterialResponse])
def list_materials(project_id: uuid.UUID, db: Session = Depends(get_db)):
    service = EntityService(db)
    try:
        return service.list_entities(project_id=project_id, kind="material")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/projects/{project_id}/materials/{material_id}", response_model=MaterialResponse)
def get_material(project_id: uuid.UUID, material_id: uuid.UUID, db: Session = Depends(get_db)):
    service = EntityService(db)
    try:
        return service.get_entity(material_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/projects/{project_id}/materials/{material_id}", status_code=204)
def delete_material(project_id: uuid.UUID, material_id: uuid.UUID, db: Session = Depends(get_db)):
    service = EntityService(db)
    try:
        service.delete_entity(material_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/materials/{material_id}/parameters", response_model=ParameterResponse, status_code=201)
def add_parameter(
    project_id: uuid.UUID,
    material_id: uuid.UUID,
    param_data: ParameterCreate,
    db: Session = Depends(get_db),
):
    service = EntityService(db)
    try:
        return service.add_parameter(
            entity_id=material_id, domain=param_data.domain, key=param_data.key,
            value_string=param_data.value_string, value_number=param_data.value_number,
            value_boolean=param_data.value_boolean,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/materials/{material_id}/parameters", response_model=List[ParameterResponse])
def list_parameters(
    project_id: uuid.UUID, material_id: uuid.UUID, db: Session = Depends(get_db)
):
    service = EntityService(db)
    try:
        return service.get_entity_parameters(material_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/projects/{project_id}/materials/{material_id}/parameters/{parameter_id}", status_code=204)
def delete_parameter(
    project_id: uuid.UUID,
    material_id: uuid.UUID,
    parameter_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = EntityService(db)
    if not service.delete_parameter(parameter_id):
        raise HTTPException(status_code=404, detail="Parameter not found")
