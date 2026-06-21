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
    type: str
    status: str = "pending"


class PlanningRunResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str
    type: str
    result: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class PlanningRunListResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str
    type: str

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
        type=request.type,
        status=request.status,
    )
    db.add(planning_run)
    db.commit()
    db.refresh(planning_run)
    return planning_run


@router.get("", response_model=List[PlanningRunListResponse])
def list_planning_runs(
    db: Session = Depends(get_db),
):
    """List all planning runs without results (to avoid traffic bloat)."""
    planning_runs = db.query(PlanningRun).all()
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
    result: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
):
    """Update a planning run's status and/or result."""
    planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
    if not planning_run:
        raise HTTPException(status_code=404, detail="Planning run not found")
    
    if status is not None:
        planning_run.status = status
    if result is not None:
        planning_run.result = result
    
    db.commit()
    db.refresh(planning_run)
    return planning_run
