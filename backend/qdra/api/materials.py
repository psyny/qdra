import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from services.material_service import MaterialService

router = APIRouter()


class MaterialResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID

    class Config:
        from_attributes = True


class ParameterCreate(BaseModel):
    domain: str
    key: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None


class ParameterResponse(BaseModel):
    id: uuid.UUID
    material_id: uuid.UUID
    domain: str
    key: str
    value_string: Optional[str]
    value_number: Optional[float]
    value_boolean: Optional[bool]

    class Config:
        from_attributes = True


@router.post("/projects/{project_id}/materials", response_model=MaterialResponse, status_code=201)
def create_material(project_id: uuid.UUID, db: Session = Depends(get_db)):
    service = MaterialService(db)
    try:
        material = service.create_material(project_id)
        return material
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/projects/{project_id}/materials", response_model=list[MaterialResponse])
def list_materials(project_id: uuid.UUID, db: Session = Depends(get_db)):
    service = MaterialService(db)
    try:
        return service.list_materials(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/materials/{material_id}", response_model=MaterialResponse)
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


@router.delete("/parameters/{parameter_id}")
def delete_parameter(parameter_id: uuid.UUID, db: Session = Depends(get_db)):
    service = MaterialService(db)
    deleted = service.delete_parameter(parameter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Parameter not found")
    return {"message": "Parameter deleted"}
