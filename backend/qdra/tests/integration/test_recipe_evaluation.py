import pytest


def test_constraint_matching_exists(client, project_ctx):
    """Test constraint matching with exists operator."""
    project_id = project_ctx["project_id"]

    # Create material with metal classification using bulk endpoint
    material_response = client.post(
        f"/api/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "classification", "key": "metal", "value_boolean": True}]}
    )
    material_id = material_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate recipe
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": [material_id]}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is True
    assert len(data["allocations"]) == 1


def test_constraint_matching_gte(client, project_ctx):
    """Test constraint matching with >= operator."""
    project_id = project_ctx["project_id"]

    # Create material with quality 78 using bulk endpoint
    material_response = client.post(
        f"/api/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "stat", "key": "quality", "value_number": 78}]}
    )
    material_id = material_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "stat", "key": "quality", "operator": ">=", "value_number": 70}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate recipe
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": [material_id]}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is True


def test_constraint_matching_lt(client, project_ctx):
    """Test constraint matching with < operator."""
    project_id = project_ctx["project_id"]

    # Create material with quality 50 using bulk endpoint
    material_response = client.post(
        f"/api/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "stat", "key": "quality", "value_number": 50}]}
    )
    material_id = material_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "stat", "key": "quality", "operator": "<", "value_number": 60}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate recipe
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": [material_id]}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is True


def test_constraint_matching_eq(client, project_ctx):
    """Test constraint matching with = operator."""
    project_id = project_ctx["project_id"]

    # Create material with name iron_ore using bulk endpoint
    material_response = client.post(
        f"/api/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
    )
    material_id = material_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ore"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate recipe
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": [material_id]}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is True


def test_quantity_matching_sufficient(client, project_ctx):
    """Test quantity matching when sufficient materials available."""
    project_id = project_ctx["project_id"]

    # Create 3 materials with metal classification using bulk endpoint
    material_ids = []
    for _ in range(3):
        material_response = client.post(
            f"/api/projects/{project_id}/materials/bulk",
            json={"parameters": [{"domain": "classification", "key": "metal", "value_boolean": True}]}
        )
        material_id = material_response.json()["id"]
        material_ids.append(material_id)

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 2,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate recipe
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": material_ids}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is True
    assert len(data["allocations"]) == 2


def test_quantity_matching_insufficient(client, project_ctx):
    """Test quantity matching when insufficient materials available."""
    project_id = project_ctx["project_id"]

    # Create 2 materials with metal classification using bulk endpoint
    material_ids = []
    for _ in range(2):
        material_response = client.post(
            f"/api/projects/{project_id}/materials/bulk",
            json={"parameters": [{"domain": "classification", "key": "metal", "value_boolean": True}]}
        )
        material_id = material_response.json()["id"]
        material_ids.append(material_id)

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 3,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate recipe
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": material_ids}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is False


def test_option_matching_or_semantics(client, project_ctx):
    """Test option matching with OR semantics - first option should match."""
    project_id = project_ctx["project_id"]

    # Create material with metal classification using bulk endpoint
    material_response = client.post(
        f"/api/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "classification", "key": "metal", "value_boolean": True}]}
    )
    material_id = material_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 2,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        },
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "precious_metal", "operator": "exists"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate recipe - should fail because option A requires 2 but only 1 available
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": [material_id]}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is False


def test_option_matching_second_option_succeeds(client, project_ctx):
    """Test option matching where second option succeeds."""
    project_id = project_ctx["project_id"]

    # Create material with precious metal classification using bulk endpoint
    material_response = client.post(
        f"/api/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "classification", "key": "precious_metal", "value_boolean": True}]}
    )
    material_id = material_response.json()["id"]

    # Create recipe
    recipe_response = client.post(f"/api/projects/{project_id}/recipes", json={})
    recipe_id = recipe_response.json()["id"]

    # Create slot
    slot_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/slots", json={"kind": "CONSUMES"}
    )
    slot_id = slot_response.json()["id"]

    # Create option A: requires 2 metals
    option_a_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options",
        json={"quantity": 2},
    )
    option_a_id = option_a_response.json()["id"]
    client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options/{option_a_id}/constraints",
        json={"domain": "classification", "key": "metal", "operator": "exists"},
    )

    # Create option B: requires 1 precious metal
    option_b_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options",
        json={"quantity": 1},
    )
    option_b_id = option_b_response.json()["id"]
    client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options/{option_b_id}/constraints",
        json={"domain": "classification", "key": "precious_metal", "operator": "exists"},
    )

    # Evaluate recipe - should succeed with option B
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": [material_id]}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is True
    # Check that option B was used
    slot_result = data["slot_results"][0]
    assert slot_result["matched_option_id"] == option_b_id


def test_slot_matching_and_semantics(client, project_ctx):
    """Test slot matching with AND semantics - all slots must succeed."""
    project_id = project_ctx["project_id"]

    # Create 2 metal materials using bulk endpoint
    metal_ids = []
    for _ in range(2):
        material_response = client.post(
            f"/api/projects/{project_id}/materials/bulk",
            json={"parameters": [{"domain": "classification", "key": "metal", "value_boolean": True}]}
        )
        material_id = material_response.json()["id"]
        metal_ids.append(material_id)

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate recipe
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": metal_ids}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is True
    assert len(data["slot_results"]) == 2
    assert all(slot["success"] for slot in data["slot_results"])


def test_slot_matching_one_slot_fails(client, project_ctx):
    """Test slot matching when one slot fails - recipe should fail."""
    project_id = project_ctx["project_id"]

    # Create 1 metal material using bulk endpoint
    material_response = client.post(
        f"/api/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "classification", "key": "metal", "value_boolean": True}]}
    )
    material_id = material_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate recipe
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": [material_id]}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is False
    # First slot should succeed, second should fail
    assert data["slot_results"][0]["success"] is True
    assert data["slot_results"][1]["success"] is False


def test_allocation_material_reuse_forbidden(client, project_ctx):
    """Test that material reuse is forbidden - same material cannot satisfy multiple slots."""
    project_id = project_ctx["project_id"]

    # Create 1 metal material using bulk endpoint
    material_response = client.post(
        f"/api/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "classification", "key": "metal", "value_boolean": True}]}
    )
    material_id = material_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate recipe - should fail because material can't be reused
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": [material_id]}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is False


def test_allocation_distinct_materials(client, project_ctx):
    """Test that distinct materials can satisfy different slots."""
    project_id = project_ctx["project_id"]

    # Create 2 metal materials using bulk endpoint
    material_ids = []
    for _ in range(2):
        material_response = client.post(
            f"/api/projects/{project_id}/materials/bulk",
            json={"parameters": [{"domain": "classification", "key": "metal", "value_boolean": True}]}
        )
        material_id = material_response.json()["id"]
        material_ids.append(material_id)

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate recipe - should succeed with distinct allocations
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": material_ids}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is True
    assert len(data["allocations"]) == 2
    # Verify allocations are to different materials
    allocated_materials = [alloc["material_id"] for alloc in data["allocations"]]
    assert len(set(allocated_materials)) == 2


def test_recipe_evaluation_single_slot_success(client, project_ctx):
    """Test recipe evaluation with single slot success."""
    project_id = project_ctx["project_id"]

    # Create material using bulk endpoint
    material_response = client.post(
        f"/api/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "classification", "key": "metal", "value_boolean": True}]}
    )
    material_id = material_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": [material_id]}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is True
    assert data["recipe_id"] == recipe_id


def test_recipe_evaluation_single_slot_failure(client, project_ctx):
    """Test recipe evaluation with single slot failure."""
    project_id = project_ctx["project_id"]

    # Create material without required classification using bulk endpoint
    material_response = client.post(
        f"/api/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "stone"}]}
    )
    material_id = material_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": [material_id]}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is False


def test_recipe_evaluation_multiple_constraints(client, project_ctx):
    """Test recipe evaluation with multiple constraints on an option (AND semantics)."""
    project_id = project_ctx["project_id"]

    # Create material with metal classification and quality >= 70 using bulk endpoint
    material_response = client.post(
        f"/api/projects/{project_id}/materials/bulk",
        json={
            "parameters": [
                {"domain": "classification", "key": "metal", "value_boolean": True},
                {"domain": "stat", "key": "quality", "value_number": 78}
            ]
        }
    )
    material_id = material_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"},
                                {"domain": "stat", "key": "quality", "operator": ">=", "value_number": 70}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": [material_id]}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is True


def test_recipe_evaluation_multiple_constraints_fail(client, project_ctx):
    """Test recipe evaluation when material doesn't satisfy all constraints."""
    project_id = project_ctx["project_id"]

    # Create material with metal classification but low quality using bulk endpoint
    material_response = client.post(
        f"/api/projects/{project_id}/materials/bulk",
        json={
            "parameters": [
                {"domain": "classification", "key": "metal", "value_boolean": True},
                {"domain": "stat", "key": "quality", "value_number": 50}
            ]
        }
    )
    material_id = material_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "classification", "key": "metal", "operator": "exists"},
                                {"domain": "stat", "key": "quality", "operator": ">=", "value_number": 70}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Evaluate
    eval_response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/evaluate", json={"materials": [material_id]}
    )
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["success"] is False
