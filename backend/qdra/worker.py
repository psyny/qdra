import json
import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from qdra.db.session import SessionLocal
from qdra.infrastructure.db.models import PlanningRun
from qdra.services.planning.output_solver_service import OutputSolverService
from qdra.domain.planning.output_solver_domain import (
    SolverRequest, SolverResponse, DomainConstraints, TargetSpec,
    SearchParameters, ScoreRules, UserVariableDef, ScoreFormulaDef
)
from qdra.domain.constraints import ConstraintSpec, ConstraintRule
from pydantic import ValidationError


def _deserialize_constraint_spec(data: Dict) -> ConstraintSpec:
    """Deserialize a dict to ConstraintSpec."""
    return ConstraintSpec(
        domain=data["domain"],
        key=data["key"],
        operator=data["operator"],
        value_string=data.get("value_string"),
        value_number=data.get("value_number"),
        value_boolean=data.get("value_boolean"),
        is_wildcard=data.get("is_wildcard", False),
    )


def _deserialize_constraint_rule(data: Dict) -> ConstraintRule:
    """Deserialize a dict to ConstraintRule."""
    constraints = [_deserialize_constraint_spec(c) for c in data.get("constraints", [])]
    return ConstraintRule(constraints=constraints)


def _deserialize_target_spec(data: Dict) -> TargetSpec:
    """Deserialize a dict to TargetSpec."""
    constraints = [_deserialize_constraint_spec(c) for c in data.get("constraints", [])]
    return TargetSpec(
        quantity=data["quantity"],
        target_type=data.get("target_type", "material"),
        constraints=constraints,
    )


def _deserialize_domain_constraints(data: Dict) -> DomainConstraints:
    """Deserialize a dict to DomainConstraints."""
    return DomainConstraints(
        do_not_expand_materials_matching=[
            _deserialize_constraint_rule(r) for r in data.get("do_not_expand_materials_matching", [])
        ],
        forbidden_materials_matching=[
            _deserialize_constraint_rule(r) for r in data.get("forbidden_materials_matching", [])
        ],
        forbidden_recipe_matching=[
            _deserialize_constraint_rule(r) for r in data.get("forbidden_recipe_matching", [])
        ],
        required_materials_matching=[
            _deserialize_constraint_rule(r) for r in data.get("required_materials_matching", [])
        ],
        required_recipe_matching=[
            _deserialize_constraint_rule(r) for r in data.get("required_recipe_matching", [])
        ],
        max_recipe_depth=data.get("max_recipe_depth", 10),
        allow_partial_recipe_execution=data.get("allow_partial_recipe_execution", False),
    )


def _deserialize_search_parameters(data: Dict) -> SearchParameters:
    """Deserialize a dict to SearchParameters."""
    return SearchParameters(
        max_recursion_depth=data.get("max_recursion_depth", 20),
        max_branch_width=data.get("max_branch_width", 10),
        allow_loops=data.get("allow_loops", False),
        max_solutions_returned=data.get("max_solutions_returned", 10),
        optimization_level=data.get("optimization_level", 0),
    )


def _deserialize_score_rules(data: Dict) -> ScoreRules:
    """Deserialize a dict to ScoreRules."""
    user_variables = [
        UserVariableDef(
            name=v["name"],
            parameter_domain=v["parameter_domain"],
            parameter_key=v["parameter_key"],
            constraints=[_deserialize_constraint_rule(r) for r in v.get("constraints", [])],
        )
        for v in data.get("user_variables", [])
    ]
    score_formulas = [
        ScoreFormulaDef(name=f["name"], formula=f["formula"])
        for f in data.get("score_formulas", [])
    ]
    return ScoreRules(user_variables=user_variables, score_formulas=score_formulas)


def _deserialize_solver_request(data: Dict) -> SolverRequest:
    """Deserialize a dict to SolverRequest with proper nested dataclass conversion."""
    target = _deserialize_target_spec(data["target"])
    domain_constraints = _deserialize_domain_constraints(data["domain_constraints"])
    search_parameters = _deserialize_search_parameters(data["search_parameters"])
    score_rules = None
    if data.get("score_rules"):
        score_rules = _deserialize_score_rules(data["score_rules"])

    return SolverRequest(
        project_id=uuid.UUID(data["project_id"]),
        target=target,
        domain_constraints=domain_constraints,
        search_parameters=search_parameters,
        score_rules=score_rules,
    )


def process_planning_run(planning_run: PlanningRun, db: Session) -> None:
    """Process a single planning run based on its type."""
    if planning_run.type == "output_solver":
        process_output_solver_run(planning_run, db)
    elif planning_run.type == "health_check_solver":
        process_health_check_run(planning_run, db)
    else:
        raise ValueError(f"Unsupported planning run type: {planning_run.type}")


def process_output_solver_run(planning_run: PlanningRun, db: Session) -> None:
    """Process an output solver planning run."""
    try:
        # Parse input JSON to SolverRequest
        input_data = planning_run.input
        if not input_data:
            raise ValueError("Input data is required for output_solver runs")

        # Convert dict to SolverRequest with proper nested dataclass conversion
        solver_request = _deserialize_solver_request(input_data)

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
                                "operator": getattr(p, 'operator', '='),
                                "value_string": p.value_string,
                                "value_number": p.value_number,
                                "value_boolean": p.value_boolean,
                                "is_wildcard": getattr(p, 'is_wildcard', False),
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
                                "operator": getattr(p, 'operator', '='),
                                "value_string": p.value_string,
                                "value_number": p.value_number,
                                "value_boolean": p.value_boolean,
                                "is_wildcard": getattr(p, 'is_wildcard', False),
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

    except ValidationError as e:
        # Input validation error
        planning_run.status = "failed"
        planning_run.error = f"Input validation error: {str(e)}"
        planning_run.finished_at = datetime.utcnow()
        db.commit()

    except ValueError as e:
        # Business logic error
        planning_run.status = "failed"
        planning_run.error = str(e)
        planning_run.finished_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        # Unexpected error
        planning_run.status = "failed"
        planning_run.error = f"Unexpected error: {type(e).__name__}: {str(e)}"
        planning_run.finished_at = datetime.utcnow()
        db.commit()


def process_health_check_run(planning_run: PlanningRun, db: Session) -> None:
    """Process a health check planning run - echoes input as result."""
    try:
        # Simply echo the input as the result
        input_data = planning_run.input or {}
        result_dict = {
            "echo": input_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Update planning run with success
        planning_run.status = "completed"
        planning_run.result = result_dict
        planning_run.finished_at = datetime.utcnow()
        planning_run.error = None
        db.commit()

    except Exception as e:
        # Unexpected error
        planning_run.status = "failed"
        planning_run.error = f"Unexpected error: {type(e).__name__}: {str(e)}"
        planning_run.finished_at = datetime.utcnow()
        db.commit()


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
