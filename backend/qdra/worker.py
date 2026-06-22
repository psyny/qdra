import json
import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from qdra.infrastructure.db.session import SessionLocal
from qdra.infrastructure.db.models import PlanningRun
from qdra.services.planning.output_solver_service import OutputSolverService
from qdra.domain.planning.output_solver_domain import SolverRequest, SolverResponse
from pydantic import ValidationError


def process_planning_run(planning_run: PlanningRun, db: Session) -> None:
    """Process a single planning run based on its type."""
    if planning_run.type == "output_solver":
        process_output_solver_run(planning_run, db)
    else:
        raise ValueError(f"Unsupported planning run type: {planning_run.type}")


def process_output_solver_run(planning_run: PlanningRun, db: Session) -> None:
    """Process an output solver planning run."""
    try:
        # Parse input JSON to SolverRequest
        input_data = planning_run.input
        if not input_data:
            raise ValueError("Input data is required for output_solver runs")

        # Convert dict to SolverRequest
        solver_request = SolverRequest(**input_data)

        # Execute the solver
        service = OutputSolverService(db)
        result: SolverResponse = service.solve(solver_request)

        # Serialize result to JSON
        result_dict = {
            "success": result.success,
            "plans": [
                {
                    "plan_id": plan.plan_id,
                    "graph_nodes": [
                        {
                            "id": n.id,
                            "kind": n.kind,
                            "material_id": str(n.material_id) if hasattr(n, "material_id") and n.material_id else None,
                            "produced_qty": n.produced_qty if hasattr(n, "produced_qty") else None,
                            "consumed_qty": n.consumed_qty if hasattr(n, "consumed_qty") else None,
                            "type": n.type.value if hasattr(n, "type") else None,
                            "recipe_id": str(n.recipe_id) if hasattr(n, "recipe_id") else None,
                            "execution_count": n.execution_count if hasattr(n, "execution_count") else None,
                            "tags": n.tags,
                            "rank": n.rank if hasattr(n, "rank") else None,
                        }
                        for n in plan.graph_nodes
                    ],
                    "material_edges": [
                        {"from_node_id": e.from_node_id, "to_node_id": e.to_node_id, "qty": e.qty}
                        for e in plan.material_edges
                    ],
                    "recipe_edges": [
                        {"from_node_id": e.from_node_id, "to_node_id": e.to_node_id, "qty": e.qty, "type": e.type.value}
                        for e in plan.recipe_edges
                    ],
                    "score": plan.score,
                }
                for plan in result.plans
            ],
            "entities": {
                "materials": {
                    str(k): {
                        "id": str(v.id),
                        "project_id": str(v.project_id),
                        "created_at": v.created_at.isoformat(),
                        "parameters": [
                            {
                                "domain": p.domain,
                                "key": p.key,
                                "operator": p.operator,
                                "value_string": p.value_string,
                                "value_number": p.value_number,
                                "value_boolean": p.value_boolean,
                                "is_wildcard": p.is_wildcard,
                            }
                            for p in v.parameters
                        ]
                    }
                    for k, v in result.entities.materials.items()
                },
                "recipes": {
                    str(k): {
                        "id": str(v.id),
                        "project_id": str(v.project_id),
                        "created_at": v.created_at.isoformat(),
                        "parameters": [
                            {
                                "domain": p.domain,
                                "key": p.key,
                                "operator": p.operator,
                                "value_string": p.value_string,
                                "value_number": p.value_number,
                                "value_boolean": p.value_boolean,
                                "is_wildcard": p.is_wildcard,
                            }
                            for p in v.parameters
                        ]
                    }
                    for k, v in result.entities.recipes.items()
                },
            },
            "discarded_plans_stats": {
                "loops": result.discarded_plans_stats.loops,
                "max_recursion_depth": result.discarded_plans_stats.max_recursion_depth,
                "max_recipe_depth": result.discarded_plans_stats.max_recipe_depth,
                "forbidden_recipes": result.discarded_plans_stats.forbidden_recipes,
                "forbidden_materials": result.discarded_plans_stats.forbidden_materials,
                "do_not_expand_materials": result.discarded_plans_stats.do_not_expand_materials,
                "max_solutions_returned": result.discarded_plans_stats.max_solutions_returned,
                "no_producers_found": result.discarded_plans_stats.no_producers_found,
            },
        }

        # Update planning run with success
        planning_run.status = "completed"
        planning_run.result = result_dict
        planning_run.finished_at = datetime.utcnow()
        planning_run.error = None
        db.commit()
        print(f"Planning run {planning_run.id} completed successfully")

    except ValidationError as e:
        # Input validation error
        planning_run.status = "failed"
        planning_run.error = f"Input validation error: {str(e)}"
        planning_run.finished_at = datetime.utcnow()
        db.commit()
        print(f"Planning run {planning_run.id} failed validation: {e}")

    except ValueError as e:
        # Business logic error
        planning_run.status = "failed"
        planning_run.error = str(e)
        planning_run.finished_at = datetime.utcnow()
        db.commit()
        print(f"Planning run {planning_run.id} failed: {e}")

    except Exception as e:
        # Unexpected error
        planning_run.status = "failed"
        planning_run.error = f"Unexpected error: {type(e).__name__}: {str(e)}"
        planning_run.finished_at = datetime.utcnow()
        db.commit()
        print(f"Planning run {planning_run.id} failed with unexpected error: {e}")


def claim_pending_run(db: Session) -> PlanningRun | None:
    """Claim a pending planning run using row locking."""
    # Use FOR UPDATE SKIP LOCKED to safely claim a job
    planning_run = db.execute(
        select(PlanningRun)
        .where(PlanningRun.status == "pending")
        .order_by(PlanningRun.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    ).scalar_one_or_none()

    if planning_run:
        # Mark as running
        planning_run.status = "running"
        planning_run.started_at = datetime.utcnow()
        db.commit()
        return planning_run

    return None


def worker_loop() -> None:
    """Main worker loop that polls planning_runs table."""
    print("Plan worker started, polling planning_runs table")

    while True:
        try:
            with SessionLocal() as db:
                planning_run = claim_pending_run(db)

                if planning_run:
                    print(f"Claimed planning run: {planning_run.id} (type: {planning_run.type})")
                    process_planning_run(planning_run, db)
                else:
                    # No pending jobs, sleep briefly
                    import time
                    time.sleep(1)

        except Exception as e:
            print(f"Error in worker loop: {e}")
            import time
            time.sleep(1)


if __name__ == "__main__":
    worker_loop()
