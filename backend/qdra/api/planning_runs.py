import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from qdra.infrastructure.db.models import PlanningRun

router = APIRouter(prefix="/api/planning-runs")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CreatePlanningRunRequest(BaseModel):
    name: Optional[str] = None
    type: str
    status: str = "pending"
    input: Optional[Dict[str, Any]] = None


class PlanningRunResponse(BaseModel):
    id: uuid.UUID
    name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str
    type: str
    input: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    model_config = {"from_attributes": True}


class PlanningRunListResponse(BaseModel):
    id: uuid.UUID
    name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str
    type: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("", response_model=PlanningRunResponse)
def create_planning_run(
    request: CreatePlanningRunRequest,
    db: Session = Depends(get_db),
):
    """Create a new planning run."""
    planning_run = PlanningRun(
        name=request.name,
        type=request.type,
        status=request.status,
        input=request.input,
    )
    db.add(planning_run)
    db.commit()
    db.refresh(planning_run)
    return planning_run


@router.get("", response_model=List[PlanningRunListResponse])
def list_planning_runs(
    type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all planning runs without results (to avoid traffic bloat). Can filter by type and status."""
    query = db.query(PlanningRun)
    if type is not None:
        query = query.filter(PlanningRun.type == type)
    if status is not None:
        query = query.filter(PlanningRun.status == status)
    planning_runs = query.all()
    return planning_runs


@router.get("/{run_id}", response_model=PlanningRunListResponse)
def get_planning_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get a single planning run without results via its ID."""
    planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
    if not planning_run:
        raise HTTPException(status_code=404, detail="Planning run not found")
    return planning_run


@router.get("/{run_id}/with-results", response_model=PlanningRunResponse)
def get_planning_run_with_results(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get a single planning run with results via its ID."""
    planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
    if not planning_run:
        raise HTTPException(status_code=404, detail="Planning run not found")
    return planning_run


@router.put("/{run_id}", response_model=PlanningRunResponse)
def update_planning_run(
    run_id: uuid.UUID,
    status: Optional[str] = None,
    input: Optional[Dict[str, Any]] = None,
    started_at: Optional[datetime] = None,
    finished_at: Optional[datetime] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Update a planning run's status, input, timing, result, and/or error."""
    planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
    if not planning_run:
        raise HTTPException(status_code=404, detail="Planning run not found")
    
    if status is not None:
        planning_run.status = status
    if input is not None:
        planning_run.input = input
    if started_at is not None:
        planning_run.started_at = started_at
    if finished_at is not None:
        planning_run.finished_at = finished_at
    if result is not None:
        planning_run.result = result
    if error is not None:
        planning_run.error = error
    
    db.commit()
    db.refresh(planning_run)
    return planning_run
