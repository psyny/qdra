def test_create_material(client):
    """Test that a material can be created."""
    # Create a project first
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]

    # Create a material
    response = client.post(f"/projects/{project_id}/materials")
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["project_id"] == project_id


def test_list_materials(client):
    """Test that materials can be listed."""
    # Create a project
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]

    # Create materials
    client.post(f"/projects/{project_id}/materials")
    client.post(f"/projects/{project_id}/materials")

    # List materials
    response = client.get(f"/projects/{project_id}/materials")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_material(client):
    """Test that a material can be retrieved."""
    # Create a project
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]

    # Create a material
    material_response = client.post(f"/projects/{project_id}/materials")
    material_id = material_response.json()["id"]

    # Get material
    response = client.get(f"/materials/{material_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == material_id


def test_add_string_parameter(client):
    """Test that a string parameter can be added to a material."""
    # Create a project and material
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]
    material_response = client.post(f"/projects/{project_id}/materials")
    material_id = material_response.json()["id"]

    # Add string parameter
    response = client.post(
        f"/materials/{material_id}/parameters",
        json={"domain": "identity", "key": "name", "value_string": "iron_ore"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "identity"
    assert data["key"] == "name"
    assert data["value_string"] == "iron_ore"
    assert data["value_number"] is None
    assert data["value_boolean"] is None


def test_add_number_parameter(client):
    """Test that a number parameter can be added to a material."""
    # Create a project and material
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]
    material_response = client.post(f"/projects/{project_id}/materials")
    material_id = material_response.json()["id"]

    # Add number parameter
    response = client.post(
        f"/materials/{material_id}/parameters",
        json={"domain": "stat", "key": "quality", "value_number": 78.5},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "stat"
    assert data["key"] == "quality"
    assert data["value_number"] == 78.5
    assert data["value_string"] is None
    assert data["value_boolean"] is None


def test_add_boolean_parameter(client):
    """Test that a boolean parameter can be added to a material."""
    # Create a project and material
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]
    material_response = client.post(f"/projects/{project_id}/materials")
    material_id = material_response.json()["id"]

    # Add boolean parameter
    response = client.post(
        f"/materials/{material_id}/parameters",
        json={"domain": "classification", "key": "metal", "value_boolean": True},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "classification"
    assert data["key"] == "metal"
    assert data["value_boolean"] is True
    assert data["value_string"] is None
    assert data["value_number"] is None


def test_reject_multiple_value_columns(client):
    """Test that multiple value columns are rejected."""
    # Create a project and material
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]
    material_response = client.post(f"/projects/{project_id}/materials")
    material_id = material_response.json()["id"]

    # Try to add parameter with multiple values
    response = client.post(
        f"/materials/{material_id}/parameters",
        json={
            "domain": "test",
            "key": "test",
            "value_string": "test",
            "value_number": 123,
        },
    )
    assert response.status_code == 400
    assert "Exactly one value" in response.json()["detail"]


def test_delete_parameter(client):
    """Test that a parameter can be deleted."""
    # Create a project and material
    project_response = client.post("/projects", json={"name": "Factory Test"})
    project_id = project_response.json()["id"]
    material_response = client.post(f"/projects/{project_id}/materials")
    material_id = material_response.json()["id"]

    # Add parameter
    param_response = client.post(
        f"/materials/{material_id}/parameters",
        json={"domain": "identity", "key": "name", "value_string": "iron_ore"},
    )
    param_id = param_response.json()["id"]

    # Delete parameter
    response = client.delete(f"/parameters/{param_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Parameter deleted"}
