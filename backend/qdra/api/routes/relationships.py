from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List
import uuid
from qdra.infrastructure.db.session import get_db
from qdra.infrastructure.db.models import Relationship

router = APIRouter()


class RelationshipCreate(BaseModel):
    source_object_id: uuid.UUID
    target_object_id: uuid.UUID
    relationship_type: str


class RelationshipResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    source_object_id: uuid.UUID
    target_object_id: uuid.UUID
    relationship_type: str

    class Config:
        from_attributes = True


@router.post("/", response_model=RelationshipResponse)
async def create_relationship(
    project_id: uuid.UUID,
    rel: RelationshipCreate,
    db: AsyncSession = Depends(get_db)
):
    db_rel = Relationship(project_id=project_id, **rel.model_dump())
    db.add(db_rel)
    await db.commit()
    await db.refresh(db_rel)
    return db_rel


@router.get("/", response_model=List[RelationshipResponse])
async def list_relationships(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Relationship).where(Relationship.project_id == project_id))
    relationships = result.scalars().all()
    return relationships
