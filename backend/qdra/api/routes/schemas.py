from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
import uuid
from qdra.infrastructure.db.session import get_db
from qdra.infrastructure.db.models import CustomType, FieldDefinition

router = APIRouter()


class TypeCreate(BaseModel):
    name: str
    description: Optional[str] = None


class TypeResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class FieldCreate(BaseModel):
    name: str
    field_type: str
    required: bool = False


class FieldResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    type_id: uuid.UUID
    name: str
    field_type: str
    required: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=TypeResponse)
async def create_type(
    project_id: uuid.UUID,
    type_data: TypeCreate,
    db: AsyncSession = Depends(get_db)
):
    db_type = CustomType(project_id=project_id, **type_data.model_dump())
    db.add(db_type)
    await db.commit()
    await db.refresh(db_type)
    return db_type


@router.get("/", response_model=List[TypeResponse])
async def list_types(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CustomType).where(CustomType.project_id == project_id))
    types = result.scalars().all()
    return types


@router.post("/{type_id}/fields", response_model=FieldResponse)
async def create_field(
    project_id: uuid.UUID,
    type_id: uuid.UUID,
    field: FieldCreate,
    db: AsyncSession = Depends(get_db)
):
    db_field = FieldDefinition(
        project_id=project_id,
        type_id=type_id,
        **field.model_dump()
    )
    db.add(db_field)
    await db.commit()
    await db.refresh(db_field)
    return db_field
