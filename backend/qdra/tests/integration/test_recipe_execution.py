import pytest


def test_consumed_materials_are_removed(client, project_ctx):
    """Verify consumed materials are removed from state."""
    project_id = project_ctx["project_id"]

    # Create two iron ore materials using bulk endpoint
    material1_response = client.post(
        f"/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
    )
    material1_id = material1_response.json()["id"]

    material2_response = client.post(
        f"/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
    )
    material2_id = material2_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 2,
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

    # Execute recipe
    exec_response = client.post(
        f"/projects/{project_id}/recipes/{recipe_id}/execute", json={"materials": [material1_id, material2_id]}
    )
    assert exec_response.status_code == 200
    data = exec_response.json()
    assert data["success"] is True
    assert set(data["consumed_material_ids"]) == {material1_id, material2_id}
    assert material1_id not in data["state_after"]
    assert material2_id not in data["state_after"]


def test_only_allocated_materials_are_removed(client, project_ctx):
    """Verify only allocated materials are removed, not others."""
    project_id = project_ctx["project_id"]

    # Create three iron ore materials using bulk endpoint
    material_ids = []
    for i in range(3):
        material_response = client.post(
            f"/projects/{project_id}/materials/bulk",
            json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
        )
        material_id = material_response.json()["id"]
        material_ids.append(material_id)

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 2,
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

    # Execute recipe with all 3 materials
    exec_response = client.post(
        f"/projects/{project_id}/recipes/{recipe_id}/execute", json={"materials": material_ids}
    )
    assert exec_response.status_code == 200
    data = exec_response.json()
    assert data["success"] is True
    assert len(data["consumed_material_ids"]) == 2
    # One material should remain in state
    assert len(data["state_after"]) == 1


def test_required_materials_remain_available(client, project_ctx):
    """Verify required materials remain in state after execution."""
    project_id = project_ctx["project_id"]

    # Create smelter material using bulk endpoint
    smelter_response = client.post(
        f"/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "smelter"}]}
    )
    smelter_id = smelter_response.json()["id"]

    # Create iron ore material using bulk endpoint
    ore_response = client.post(
        f"/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
    )
    ore_id = ore_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "smelter"}
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
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ore"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Execute recipe
    exec_response = client.post(
        f"/projects/{project_id}/recipes/{recipe_id}/execute", json={"materials": [smelter_id, ore_id]}
    )
    assert exec_response.status_code == 200
    data = exec_response.json()
    assert data["success"] is True
    assert smelter_id in data["required_material_ids"]
    assert smelter_id in data["state_after"]  # Smelter remains
    assert ore_id not in data["state_after"]  # Ore is consumed


def test_required_materials_can_participate_in_future_executions(client, project_ctx):
    """Verify required materials remain available for future executions."""
    project_id = project_ctx["project_id"]

    # Create smelter material using bulk endpoint
    smelter_response = client.post(
        f"/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "smelter"}]}
    )
    smelter_id = smelter_response.json()["id"]

    # Create two iron ore materials using bulk endpoint
    ore_ids = []
    for i in range(2):
        ore_response = client.post(
            f"/projects/{project_id}/materials/bulk",
            json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
        )
        ore_id = ore_response.json()["id"]
        ore_ids.append(ore_id)

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "smelter"}
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
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ore"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Execute recipe with first ore
    exec_response = client.post(
        f"/projects/{project_id}/recipes/{recipe_id}/execute", json={"materials": [smelter_id, ore_ids[0]]}
    )
    assert exec_response.status_code == 200
    data1 = exec_response.json()
    assert data1["success"] is True
    assert smelter_id in data1["state_after"]

    # Execute again with second ore - smelter should still be available
    exec_response2 = client.post(
        f"/projects/{project_id}/recipes/{recipe_id}/execute", json={"materials": [smelter_id, ore_ids[1]]}
    )
    assert exec_response2.status_code == 200
    data2 = exec_response2.json()
    assert data2["success"] is True
    assert smelter_id in data2["state_after"]


def test_produced_materials_are_created(client, project_ctx):
    """Verify produced materials are created."""
    project_id = project_ctx["project_id"]

    # Create iron ore material using bulk endpoint
    ore_response = client.post(
        f"/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
    )
    ore_id = ore_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
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
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ingot"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Execute recipe
    exec_response = client.post(
        f"/projects/{project_id}/recipes/{recipe_id}/execute", json={"materials": [ore_id]}
    )
    assert exec_response.status_code == 200
    data = exec_response.json()
    assert data["success"] is True
    assert len(data["produced_material_ids"]) == 1
    # Verify the produced material has correct parameters
    produced_id = data["produced_material_ids"][0]
    param_response = client.get(f"/projects/{project_id}/materials/{produced_id}/parameters")
    params = param_response.json()
    assert any(p["domain"] == "identity" and p["key"] == "name" and p["value_string"] == "iron_ingot" for p in params)


def test_produced_material_parameters_are_correct(client, project_ctx):
    """Verify produced material parameters match constraints."""
    project_id = project_ctx["project_id"]

    # Create iron ore material using bulk endpoint
    ore_response = client.post(
        f"/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
    )
    ore_id = ore_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
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
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ingot"},
                                {"domain": "classification", "key": "metal", "operator": "=", "value_boolean": True}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Execute recipe
    exec_response = client.post(
        f"/projects/{project_id}/recipes/{recipe_id}/execute", json={"materials": [ore_id]}
    )
    assert exec_response.status_code == 200
    data = exec_response.json()
    assert data["success"] is True
    
    # Verify the produced material has both parameters
    produced_id = data["produced_material_ids"][0]
    param_response = client.get(f"/projects/{project_id}/materials/{produced_id}/parameters")
    params = param_response.json()
    assert any(p["domain"] == "identity" and p["key"] == "name" and p["value_string"] == "iron_ingot" for p in params)
    assert any(p["domain"] == "classification" and p["key"] == "metal" and p["value_boolean"] is True for p in params)


def test_multiple_produced_materials_can_be_created(client, project_ctx):
    """Verify multiple materials can be produced from a single slot."""
    project_id = project_ctx["project_id"]

    # Create iron ore material using bulk endpoint
    ore_response = client.post(
        f"/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
    )
    ore_id = ore_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
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
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 3,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ingot"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Execute recipe
    exec_response = client.post(
        f"/projects/{project_id}/recipes/{recipe_id}/execute", json={"materials": [ore_id]}
    )
    assert exec_response.status_code == 200
    data = exec_response.json()
    assert data["success"] is True
    assert len(data["produced_material_ids"]) == 3


def test_execution_failure_does_not_modify_state(client, project_ctx):
    """Verify execution failure leaves state unchanged."""
    project_id = project_ctx["project_id"]

    # Create iron ore material using bulk endpoint
    ore_response = client.post(
        f"/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
    )
    ore_id = ore_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "smelter"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Execute recipe - should fail
    exec_response = client.post(
        f"/projects/{project_id}/recipes/{recipe_id}/execute", json={"materials": [ore_id]}
    )
    assert exec_response.status_code == 200
    data = exec_response.json()
    assert data["success"] is False
    assert data["state_before"] == data["state_after"]
    assert len(data["consumed_material_ids"]) == 0
    assert len(data["produced_material_ids"]) == 0


def test_no_materials_removed_on_failure(client, project_ctx):
    """Verify no materials are removed when execution fails."""
    project_id = project_ctx["project_id"]

    # Create two iron ore materials using bulk endpoint
    material_ids = []
    for i in range(2):
        material_response = client.post(
            f"/projects/{project_id}/materials/bulk",
            json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
        )
        material_id = material_response.json()["id"]
        material_ids.append(material_id)

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 3,
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

    # Execute recipe - should fail
    exec_response = client.post(
        f"/projects/{project_id}/recipes/{recipe_id}/execute", json={"materials": material_ids}
    )
    assert exec_response.status_code == 200
    data = exec_response.json()
    assert data["success"] is False
    assert set(data["state_after"]) == set(material_ids)
    assert len(data["consumed_material_ids"]) == 0


def test_no_materials_created_on_failure(client, project_ctx):
    """Verify no materials are created when execution fails."""
    project_id = project_ctx["project_id"]

    # Create iron ore material using bulk endpoint
    ore_response = client.post(
        f"/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
    )
    ore_id = ore_response.json()["id"]

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "smelter"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ingot"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Execute recipe - should fail
    exec_response = client.post(
        f"/projects/{project_id}/recipes/{recipe_id}/execute", json={"materials": [ore_id]}
    )
    assert exec_response.status_code == 200
    data = exec_response.json()
    assert data["success"] is False
    assert len(data["produced_material_ids"]) == 0


def test_state_transition_complete(client, project_ctx):
    """Verify complete state transition: 2 iron ore + 1 smelter -> 1 smelter + 1 iron ingot."""
    project_id = project_ctx["project_id"]

    # Create smelter using bulk endpoint
    smelter_response = client.post(
        f"/projects/{project_id}/materials/bulk",
        json={"parameters": [{"domain": "identity", "key": "name", "value_string": "smelter"}]}
    )
    smelter_id = smelter_response.json()["id"]

    # Create two iron ore using bulk endpoint
    ore_ids = []
    for i in range(2):
        ore_response = client.post(
            f"/projects/{project_id}/materials/bulk",
            json={"parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]}
        )
        ore_id = ore_response.json()["id"]
        ore_ids.append(ore_id)

    # Create recipe using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 2,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ore"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "smelter"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ingot"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]

    # Execute recipe
    exec_response = client.post(
        f"/projects/{project_id}/recipes/{recipe_id}/execute", json={"materials": [smelter_id] + ore_ids}
    )
    assert exec_response.status_code == 200
    data = exec_response.json()
    assert data["success"] is True
    
    # Verify state transition
    # Before: 1 smelter + 2 iron ore = 3 materials
    assert len(data["state_before"]) == 3
    
    # After: 1 smelter + 1 iron ingot = 2 materials
    assert len(data["state_after"]) == 2
    
    # Smelter should remain
    assert smelter_id in data["state_after"]
    
    # Iron ore should be consumed
    assert ore_ids[0] not in data["state_after"]
    assert ore_ids[1] not in data["state_after"]
    
    # Iron ingot should be produced
    assert len(data["produced_material_ids"]) == 1
    assert data["produced_material_ids"][0] in data["state_after"]
