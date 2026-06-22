import pytest
import uuid
from qdra.services.constraint_resolution_service import ConstraintResolutionService
from qdra.domain.planning.output_solver_domain import ConstraintSpec
from tests.integration.datasets import create_medium_size_planning_dataset


def test_find_materials_by_category_constraint(client, project_ctx, db):
    """Test finding materials by a simple category constraint."""
    project_id = project_ctx["project_id"]

    # Create test dataset
    dataset = create_medium_size_planning_dataset(client, project_id)
    materials = dataset["materials"]

    # Initialize service
    service = ConstraintResolutionService(db)

    # Find materials with category "final_product"
    constraints = [
        ConstraintSpec(
            domain="identity",
            key="category",
            operator="=",
            value_string="final_product"
        )
    ]

    result = service.find_materials_by_constraints(constraints, project_id)

    # Should return final_product_1 and final_product_2
    assert len(result) == 2
    assert uuid.UUID(materials["final_product_1"]["id"]) in result
    assert uuid.UUID(materials["final_product_2"]["id"]) in result


def test_find_materials_by_multiple_constraints(client, project_ctx, db):
    """Test finding materials with multiple constraints (AND logic)."""
    project_id = project_ctx["project_id"]

    # Create test dataset
    dataset = create_medium_size_planning_dataset(client, project_id)
    materials = dataset["materials"]

    # Initialize service
    service = ConstraintResolutionService(db)

    # Find materials with category "intermediate" AND name "intermediate_1"
    constraints = [
        ConstraintSpec(
            domain="identity",
            key="category",
            operator="=",
            value_string="intermediate"
        ),
        ConstraintSpec(
            domain="identity",
            key="name",
            operator="=",
            value_string="intermediate_1"
        )
    ]

    result = service.find_materials_by_constraints(constraints, project_id)

    # Should return only intermediate_1
    assert len(result) == 1
    assert uuid.UUID(materials["intermediate_1"]["id"]) in result


def test_find_materials_by_system_id_constraint(client, project_ctx, db):
    """Test finding materials by __system__ id constraint."""
    project_id = project_ctx["project_id"]

    # Create test dataset
    dataset = create_medium_size_planning_dataset(client, project_id)
    materials = dataset["materials"]

    # Initialize service
    service = ConstraintResolutionService(db)

    # Find material by specific ID using __system__ domain
    constraints = [
        ConstraintSpec(
            domain="__system__",
            key="id",
            operator="=",
            value_string=str(materials["raw_resource"]["id"])
        )
    ]

    result = service.find_materials_by_constraints(constraints, project_id)

    # Should return only raw_resource
    assert len(result) == 1
    assert uuid.UUID(materials["raw_resource"]["id"]) in result
