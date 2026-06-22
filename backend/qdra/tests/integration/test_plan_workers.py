import pytest
import time
from datetime import datetime
from sqlalchemy.orm import Session
from qdra.infrastructure.db.models import PlanningRun


def test_health_check_solver(client, db: Session):
    """Test that the worker can process a health_check planning run via API."""
    
    # Create a health check planning run via API
    test_input = {"test_key": "test_value", "number": 42}
    
    response = client.post(
        "/api/planning-runs",
        json={
            "name": "Health check test",
            "type": "health_check_solver",
            "input": test_input,
        }
    )
    
    assert response.status_code == 200
    planning_run_data = response.json()
    run_id = planning_run_data["id"]
    
    # Wait for the worker to process it (max 30 seconds)
    max_wait = 30
    start = time.time()
    
    while time.time() - start < max_wait:
        planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
        if planning_run.status in ["completed", "failed"]:
            break
        time.sleep(0.5)
    
    # Verify the run was processed
    planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
    assert planning_run.status == "completed", f"Run status is {planning_run.status}, error: {planning_run.error}"
    assert planning_run.started_at is not None
    assert planning_run.finished_at is not None
    assert planning_run.error is None
    
    # Verify the result echoes the input
    assert planning_run.result is not None
    assert "echo" in planning_run.result
    assert planning_run.result["echo"] == test_input
    assert "timestamp" in planning_run.result


def test_health_check_solver_with_empty_input(client, db: Session):
    """Test that the worker handles empty input gracefully via API."""
    
    # Create a health check planning run with no input via API
    response = client.post(
        "/api/planning-runs",
        json={
            "name": "Health check test - empty input",
            "type": "health_check_solver",
            "input": None,
        }
    )
    
    assert response.status_code == 200
    planning_run_data = response.json()
    run_id = planning_run_data["id"]
    
    # Wait for the worker to process it
    max_wait = 30
    start = time.time()
    
    while time.time() - start < max_wait:
        planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
        if planning_run.status in ["completed", "failed"]:
            break
        time.sleep(0.5)
    
    # Verify the run was processed
    planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
    assert planning_run.status == "completed", f"Run status is {planning_run.status}, error: {planning_run.error}"
    assert planning_run.result is not None
    assert planning_run.result["echo"] == {}


def test_health_check_solver_with_complex_input(client, db: Session):
    """Test that the worker handles complex nested JSON input via API."""
    
    # Create a health check planning run with complex input via API
    test_input = {
        "nested": {
            "level1": {
                "level2": {
                    "value": "deep"
                }
            }
        },
        "array": [1, 2, 3, {"key": "value"}],
        "boolean": True,
        "null": None,
    }
    
    response = client.post(
        "/api/planning-runs",
        json={
            "name": "Health check test - complex input",
            "type": "health_check_solver",
            "input": test_input,
        }
    )
    
    assert response.status_code == 200
    planning_run_data = response.json()
    run_id = planning_run_data["id"]
    
    # Wait for the worker to process it
    max_wait = 30
    start = time.time()
    
    while time.time() - start < max_wait:
        planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
        if planning_run.status in ["completed", "failed"]:
            break
        time.sleep(0.5)
    
    # Verify the run was processed
    planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
    assert planning_run.status == "completed", f"Run status is {planning_run.status}, error: {planning_run.error}"
    assert planning_run.result is not None
    assert planning_run.result["echo"] == test_input


def test_planning_run_timing_fields(client, db: Session):
    """Test that timing fields are set correctly during processing via API."""
    
    # Create a health check planning run via API
    response = client.post(
        "/api/planning-runs",
        json={
            "name": "Timing test",
            "type": "health_check_solver",
            "input": {"test": "timing"},
        }
    )
    
    assert response.status_code == 200
    planning_run_data = response.json()
    run_id = planning_run_data["id"]
    
    # Get initial state
    planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
    created_at = planning_run.created_at
    assert planning_run.started_at is None
    assert planning_run.finished_at is None
    
    # Wait for the worker to process it
    max_wait = 30
    start = time.time()
    
    while time.time() - start < max_wait:
        planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
        if planning_run.status in ["completed", "failed"]:
            break
        time.sleep(0.5)
    
    # Verify timing fields
    planning_run = db.query(PlanningRun).filter(PlanningRun.id == run_id).first()
    assert planning_run.status == "completed"
    assert planning_run.started_at is not None
    assert planning_run.finished_at is not None
    assert planning_run.started_at >= created_at
    assert planning_run.finished_at >= planning_run.started_at
