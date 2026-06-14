def test_create_recipe(client):
    """Test that a recipe can be created."""
    # Create a project
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]

    # Create a recipe
    response = client.post(f"/projects/{project_id}/recipes", json={"name": "Smelting"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Smelting"
    assert data["project_id"] == project_id
    assert "id" in data


def test_list_recipes(client):
    """Test that recipes can be listed."""
    # Create a project
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]

    # Create recipes
    client.post(f"/projects/{project_id}/recipes", json={"name": "Recipe 1"})
    client.post(f"/projects/{project_id}/recipes", json={"name": "Recipe 2"})

    # List recipes
    response = client.get(f"/projects/{project_id}/recipes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_recipe(client):
    """Test that a recipe can be retrieved."""
    # Create a project
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]

    # Create a recipe
    recipe_response = client.post(f"/projects/{project_id}/recipes", json={"name": "Smelting"})
    recipe_id = recipe_response.json()["id"]

    # Get recipe
    response = client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == recipe_id


def test_create_slot(client):
    """Test that a slot can be created."""
    # Create a project and recipe
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]
    recipe_response = client.post(f"/projects/{project_id}/recipes", json={"name": "Smelting"})
    recipe_id = recipe_response.json()["id"]

    # Create a slot
    response = client.post(f"/recipes/{recipe_id}/slots", json={"kind": "CONSUMES"})
    assert response.status_code == 201
    data = response.json()
    assert data["kind"] == "CONSUMES"
    assert data["recipe_id"] == recipe_id


def test_create_option(client):
    """Test that an option can be created."""
    # Create a project, recipe, and slot
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]
    recipe_response = client.post(f"/projects/{project_id}/recipes", json={"name": "Smelting"})
    recipe_id = recipe_response.json()["id"]
    slot_response = client.post(f"/recipes/{recipe_id}/slots", json={"kind": "CONSUMES"})
    slot_id = slot_response.json()["id"]

    # Create an option
    response = client.post(f"/slots/{slot_id}/options", json={"quantity": 2.0})
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 2.0
    assert data["slot_id"] == slot_id


def test_create_constraint(client):
    """Test that a constraint can be created."""
    # Create a project, recipe, slot, and option
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]
    recipe_response = client.post(f"/projects/{project_id}/recipes", json={"name": "Smelting"})
    recipe_id = recipe_response.json()["id"]
    slot_response = client.post(f"/recipes/{recipe_id}/slots", json={"kind": "CONSUMES"})
    slot_id = slot_response.json()["id"]
    option_response = client.post(f"/slots/{slot_id}/options", json={"quantity": 2.0})
    option_id = option_response.json()["id"]

    # Create a constraint
    response = client.post(
        f"/options/{option_id}/constraints",
        json={
            "domain": "classification",
            "key": "metal",
            "operator": "exists",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "classification"
    assert data["key"] == "metal"
    assert data["operator"] == "exists"
    assert data["option_id"] == option_id


def test_add_recipe_parameter(client):
    """Test that a parameter can be added to a recipe."""
    # Create a project and recipe
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]
    recipe_response = client.post(f"/projects/{project_id}/recipes", json={"name": "Smelting"})
    recipe_id = recipe_response.json()["id"]

    # Add a parameter
    response = client.post(
        f"/recipes/{recipe_id}/parameters",
        json={
            "domain": "identity",
            "key": "name",
            "value_string": "steel_ingot",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "identity"
    assert data["key"] == "name"
    assert data["value_string"] == "steel_ingot"
    assert data["recipe_id"] == recipe_id


def test_list_recipe_parameters(client):
    """Test that recipe parameters can be listed."""
    # Create a project and recipe
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]
    recipe_response = client.post(f"/projects/{project_id}/recipes", json={"name": "Smelting"})
    recipe_id = recipe_response.json()["id"]

    # Add parameters
    client.post(
        f"/recipes/{recipe_id}/parameters",
        json={"domain": "identity", "key": "name", "value_string": "steel_ingot"},
    )
    client.post(
        f"/recipes/{recipe_id}/parameters",
        json={"domain": "classification", "key": "metal", "value_boolean": True},
    )

    # List parameters
    response = client.get(f"/recipes/{recipe_id}/parameters")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_delete_recipe_parameter(client):
    """Test that a recipe parameter can be deleted."""
    # Create a project and recipe
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]
    recipe_response = client.post(f"/projects/{project_id}/recipes", json={"name": "Smelting"})
    recipe_id = recipe_response.json()["id"]

    # Add a parameter
    param_response = client.post(
        f"/recipes/{recipe_id}/parameters",
        json={"domain": "identity", "key": "name", "value_string": "steel_ingot"},
    )
    parameter_id = param_response.json()["id"]

    # Delete the parameter
    response = client.delete(f"/recipe_parameters/{parameter_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Parameter deleted"

    # Verify it's gone
    list_response = client.get(f"/recipes/{recipe_id}/parameters")
    assert len(list_response.json()) == 0


def test_create_recipe_bulk_with_parameters(client):
    """Test that a recipe can be created with parameters via bulk endpoint."""
    # Create a project
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]

    # Create a recipe with parameters
    response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "Smelting",
            "parameters": [
                {"domain": "identity", "key": "name", "value_string": "steel_ingot"},
                {"domain": "classification", "key": "metal", "value_boolean": True},
            ],
            "slots": [],
        },
    )
    assert response.status_code == 201
    recipe_id = response.json()["id"]

    # Verify parameters were created
    params_response = client.get(f"/recipes/{recipe_id}/parameters")
    assert params_response.status_code == 200
    params = params_response.json()
    assert len(params) == 2
