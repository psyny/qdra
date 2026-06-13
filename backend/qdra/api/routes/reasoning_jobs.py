from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid
import redis.asyncio as redis
from qdra.infrastructure.db.session import get_db
from qdra.infrastructure.db.models import ReasoningJob
from qdra.infrastructure.config.settings import settings

router = APIRouter()


class JobCreate(BaseModel):
    pass  # Add job-specific parameters later


class JobResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    status: str

    class Config:
        from_attributes = True


class JobResultResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    status: str
    result: Optional[str]
    error_message: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=JobResponse)
async def create_job(
    project_id: uuid.UUID,
    job: JobCreate,
    db: AsyncSession = Depends(get_db)
):
    # Create job in database
    db_job = ReasoningJob(project_id=project_id, status="queued")
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)

    # Push job to Redis queue
    r = redis.from_url(settings.redis_url, decode_responses=True)
    await r.rpush(settings.graph_job_queue, str(db_job.id))

    return db_job


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ReasoningJob).where(
            ReasoningJob.id == job_id,
            ReasoningJob.project_id == project_id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ReasoningJob).where(
            ReasoningJob.id == job_id,
            ReasoningJob.project_id == project_id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
