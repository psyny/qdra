import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from infrastructure.db.models import PlanningRun


class PlanningRunService:
    def __init__(self, db: Session):
        self.db = db

    def create_planning_run(
        self,
        name: Optional[str],
        type: str,
        status: str = "pending",
        input: Optional[Dict[str, Any]] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> PlanningRun:
        """Create a new planning run."""
        planning_run = PlanningRun(
            name=name,
            type=type,
            status=status,
            input=input,
            project_id=project_id,
        )
        self.db.add(planning_run)
        self.db.commit()
        self.db.refresh(planning_run)
        return planning_run

    def list_planning_runs(
        self,
        type: Optional[str] = None,
        status: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> List[PlanningRun]:
        """List all planning runs without results (to avoid traffic bloat). Can filter by type, status, and project_id."""
        query = self.db.query(PlanningRun)
        if type is not None:
            query = query.filter(PlanningRun.type == type)
        if status is not None:
            query = query.filter(PlanningRun.status == status)
        if project_id is not None:
            query = query.filter(PlanningRun.project_id == project_id)
        return query.all()

    def get_planning_run(self, run_id: uuid.UUID) -> Optional[PlanningRun]:
        """Get a single planning run without results via its ID."""
        return self.db.query(PlanningRun).filter(PlanningRun.id == run_id).first()

    def get_planning_run_with_results(self, run_id: uuid.UUID) -> Optional[PlanningRun]:
        """Get a single planning run with results via its ID."""
        return self.db.query(PlanningRun).filter(PlanningRun.id == run_id).first()

    def update_planning_run(
        self,
        run_id: uuid.UUID,
        status: Optional[str] = None,
        input: Optional[Dict[str, Any]] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[PlanningRun]:
        """Update a planning run's status, input, timing, result, and/or error."""
        planning_run = self.db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
        if not planning_run:
            return None

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

        self.db.commit()
        self.db.refresh(planning_run)
        return planning_run

    def delete_planning_run(self, run_id: uuid.UUID) -> bool:
        """Delete a planning run by its ID."""
        planning_run = self.db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
        if not planning_run:
            return False

        self.db.delete(planning_run)
        self.db.commit()
        return True
