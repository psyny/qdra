from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
import uuid
from qdra.infrastructure.db.session import get_db
from qdra.infrastructure.db.models import Object

router = APIRouter()


class ObjectCreate(BaseModel):
    name: str
    type_id: uuid.UUID
    data: Optional[str] = None


class ObjectResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    type_id: uuid.UUID
    name: str
    data: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=ObjectResponse)
async def create_object(
    project_id: uuid.UUID,
    obj: ObjectCreate,
    db: AsyncSession = Depends(get_db)
):
    db_obj = Object(project_id=project_id, **obj.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.get("/", response_model=List[ObjectResponse])
async def list_objects(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Object).where(Object.project_id == project_id))
    objects = result.scalars().all()
    return objects


@router.get("/{object_id}", response_model=ObjectResponse)
async def get_object(
    project_id: uuid.UUID,
    object_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Object).where(
            Object.id == object_id,
            Object.project_id == project_id
        )
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    return obj
