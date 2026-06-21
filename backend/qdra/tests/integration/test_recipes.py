def test_create_recipe(client, project_ctx):
    """Test that a recipe can be created."""
    project_id = project_ctx["project_id"]
    response = client.post(f"/api/projects/{project_id}/recipes", json={})

    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == project_id
    assert "id" in data
    assert data["kind"] == "recipe"


def test_list_recipes(client, project_ctx):
    """Test that recipes can be listed."""
    project_id = project_ctx["project_id"]
    client.post(f"/api/projects/{project_id}/recipes", json={})
    client.post(f"/api/projects/{project_id}/recipes", json={})
    response = client.get(f"/api/projects/{project_id}/recipes")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_recipe(client, project_ctx):
    """Test that a recipe can be retrieved."""
    project_id = project_ctx["project_id"]
    recipe_id = client.post(f"/api/projects/{project_id}/recipes", json={}).json()["id"]
    response = client.get(f"/api/projects/{project_id}/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["id"] == recipe_id


def test_create_slot(client, project_ctx):
    """Test that a slot can be created."""
    project_id = project_ctx["project_id"]
    recipe_id = client.post(f"/api/projects/{project_id}/recipes", json={}).json()["id"]
    response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/slots", json={"kind": "CONSUMES"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["kind"] == "consumes"
    assert data["recipe_entity_id"] == recipe_id


def test_create_option(client, project_ctx):
    """Test that an option can be created."""
    project_id = project_ctx["project_id"]
    recipe_id = client.post(f"/api/projects/{project_id}/recipes", json={}).json()["id"]
    slot_id = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/slots", json={"kind": "CONSUMES"}
    ).json()["id"]
    response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options",
        json={"quantity": 2.0},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 2.0
    assert data["slot_id"] == slot_id


def test_create_constraint(client, project_ctx):
    """Test that a constraint can be created."""
    project_id = project_ctx["project_id"]
    recipe_id = client.post(f"/api/projects/{project_id}/recipes", json={}).json()["id"]
    slot_id = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/slots", json={"kind": "CONSUMES"}
    ).json()["id"]
    option_id = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options",
        json={"quantity": 2.0},
    ).json()["id"]
    response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options/{option_id}/constraints",
        json={"domain": "classification", "key": "metal", "operator": "exists"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "classification"
    assert data["key"] == "metal"
    assert data["operator"] == "exists"
    assert data["option_id"] == option_id


def test_add_recipe_parameter(client, project_ctx):
    """Test that a parameter can be added to a recipe."""
    project_id = project_ctx["project_id"]
    recipe_id = client.post(f"/api/projects/{project_id}/recipes", json={}).json()["id"]
    response = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/parameters",
        json={"domain": "identity", "key": "name", "value_string": "steel_ingot"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "identity"
    assert data["key"] == "name"
    assert data["value_string"] == "steel_ingot"
    assert data["entity_id"] == recipe_id


def test_list_recipe_parameters(client, project_ctx):
    """Test that recipe parameters can be listed."""
    project_id = project_ctx["project_id"]
    recipe_id = client.post(f"/api/projects/{project_id}/recipes", json={}).json()["id"]
    client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/parameters",
        json={"domain": "identity", "key": "name", "value_string": "steel_ingot"},
    )
    client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/parameters",
        json={"domain": "classification", "key": "metal", "value_boolean": True},
    )
    response = client.get(f"/api/projects/{project_id}/recipes/{recipe_id}/parameters")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_delete_recipe_parameter(client, project_ctx):
    """Test that a recipe parameter can be deleted."""
    project_id = project_ctx["project_id"]
    recipe_id = client.post(f"/api/projects/{project_id}/recipes", json={}).json()["id"]
    parameter_id = client.post(
        f"/api/projects/{project_id}/recipes/{recipe_id}/parameters",
        json={"domain": "identity", "key": "name", "value_string": "steel_ingot"},
    ).json()["id"]
    response = client.delete(
        f"/api/projects/{project_id}/recipes/{recipe_id}/parameters/{parameter_id}"
    )
    assert response.status_code == 204
    list_response = client.get(f"/api/projects/{project_id}/recipes/{recipe_id}/parameters")
    assert len(list_response.json()) == 0


def test_create_recipe_bulk_with_parameters(client, project_ctx):
    """Test that a recipe can be created with parameters via bulk endpoint."""
    project_id = project_ctx["project_id"]
    response = client.post(
        f"/api/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [
                {"domain": "identity", "key": "name", "value_string": "steel_ingot"},
                {"domain": "classification", "key": "metal", "value_boolean": True},
            ],
            "slots": [],
        },
    )
    assert response.status_code == 201
    recipe_id = response.json()["id"]
    params_response = client.get(f"/api/projects/{project_id}/recipes/{recipe_id}/parameters")
    assert params_response.status_code == 200
    assert len(params_response.json()) == 2
