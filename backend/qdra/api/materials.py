import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from services.material_service import MaterialService

router = APIRouter()


class ImageMetadata(BaseModel):
    id: uuid.UUID
    url: str
    mime_type: str
    alt_text: Optional[str] = None


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    image: Optional[ImageMetadata] = None


class ParameterCreate(BaseModel):
    domain: str
    key: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None


class MaterialBulkCreate(BaseModel):
    parameters: list[ParameterCreate] = []


class ParameterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    material_id: uuid.UUID
    domain: str
    key: str
    value_string: Optional[str]
    value_number: Optional[float]
    value_boolean: Optional[bool]


@router.post("/projects/{project_id}/materials", response_model=MaterialResponse, status_code=201)
def create_material(project_id: uuid.UUID, db: Session = Depends(get_db)):
    service = MaterialService(db)
    try:
        material = service.create_material(project_id)
        return material
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/materials/bulk", response_model=MaterialResponse, status_code=201)
def create_material_bulk(project_id: uuid.UUID, material_data: MaterialBulkCreate, db: Session = Depends(get_db)):
    service = MaterialService(db)
    try:
        material = service.create_material(project_id)

        for param_data in material_data.parameters:
            service.add_parameter(
                material_id=material.id,
                domain=param_data.domain,
                key=param_data.key,
                value_string=param_data.value_string,
                value_number=param_data.value_number,
                value_boolean=param_data.value_boolean,
            )

        return material
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/materials")
def list_materials(project_id: uuid.UUID, db: Session = Depends(get_db)):
    service = MaterialService(db)
    try:
        return service.list_materials(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/materials/{material_id}")
def get_material(material_id: uuid.UUID, db: Session = Depends(get_db)):
    service = MaterialService(db)
    try:
        return service.get_material(material_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/materials/{material_id}/parameters", response_model=ParameterResponse, status_code=201)
def add_parameter(
    material_id: uuid.UUID, param_data: ParameterCreate, db: Session = Depends(get_db)
):
    service = MaterialService(db)
    try:
        parameter = service.add_parameter(
            material_id=material_id,
            domain=param_data.domain,
            key=param_data.key,
            value_string=param_data.value_string,
            value_number=param_data.value_number,
            value_boolean=param_data.value_boolean,
        )
        return parameter
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/materials/{material_id}/parameters", response_model=list[ParameterResponse])
def list_parameters(material_id: uuid.UUID, db: Session = Depends(get_db)):
    service = MaterialService(db)
    try:
        return service.get_material_parameters(material_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/parameters/{parameter_id}")
def delete_parameter(parameter_id: uuid.UUID, db: Session = Depends(get_db)):
    service = MaterialService(db)
    deleted = service.delete_parameter(parameter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Parameter not found")
    return {"message": "Parameter deleted"}
