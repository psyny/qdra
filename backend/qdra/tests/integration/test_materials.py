def test_create_material(client, project_ctx):
    """Test that a material can be created."""
    project_id = project_ctx["project_id"]
    response = client.post(f"/api/projects/{project_id}/materials", json={})
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["project_id"] == project_id
    assert data["kind"] == "material"


def test_list_materials(client, project_ctx):
    """Test that materials can be listed."""
    project_id = project_ctx["project_id"]
    client.post(f"/api/projects/{project_id}/materials", json={})
    client.post(f"/api/projects/{project_id}/materials", json={})
    response = client.get(f"/api/projects/{project_id}/materials")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_material(client, project_ctx):
    """Test that a material can be retrieved."""
    project_id = project_ctx["project_id"]
    material_id = client.post(f"/api/projects/{project_id}/materials", json={}).json()["id"]
    response = client.get(f"/api/projects/{project_id}/materials/{material_id}")
    assert response.status_code == 200
    assert response.json()["id"] == material_id


def test_add_string_parameter(client, project_ctx):
    """Test that a string parameter can be added to a material."""
    project_id = project_ctx["project_id"]
    material_id = client.post(f"/api/projects/{project_id}/materials", json={}).json()["id"]
    response = client.post(
        f"/api/projects/{project_id}/materials/{material_id}/parameters",
        json={"domain": "identity", "key": "name", "value_string": "iron_ore"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "identity"
    assert data["key"] == "name"
    assert data["value_string"] == "iron_ore"
    assert data["value_number"] is None
    assert data["value_boolean"] is None


def test_add_number_parameter(client, project_ctx):
    """Test that a number parameter can be added to a material."""
    project_id = project_ctx["project_id"]
    material_id = client.post(f"/api/projects/{project_id}/materials", json={}).json()["id"]
    response = client.post(
        f"/api/projects/{project_id}/materials/{material_id}/parameters",
        json={"domain": "stat", "key": "quality", "value_number": 78.5},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "stat"
    assert data["key"] == "quality"
    assert data["value_number"] == 78.5
    assert data["value_string"] is None
    assert data["value_boolean"] is None


def test_add_boolean_parameter(client, project_ctx):
    """Test that a boolean parameter can be added to a material."""
    project_id = project_ctx["project_id"]
    material_id = client.post(f"/api/projects/{project_id}/materials", json={}).json()["id"]
    response = client.post(
        f"/api/projects/{project_id}/materials/{material_id}/parameters",
        json={"domain": "classification", "key": "metal", "value_boolean": True},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "classification"
    assert data["key"] == "metal"
    assert data["value_boolean"] is True
    assert data["value_string"] is None
    assert data["value_number"] is None


def test_reject_multiple_value_columns(client, project_ctx):
    """Test that multiple value columns are rejected."""
    project_id = project_ctx["project_id"]
    material_id = client.post(f"/api/projects/{project_id}/materials", json={}).json()["id"]
    response = client.post(
        f"/api/projects/{project_id}/materials/{material_id}/parameters",
        json={"domain": "test", "key": "test", "value_string": "test", "value_number": 123},
    )
    assert response.status_code == 400
    assert "Exactly one value" in response.json()["detail"]


def test_delete_parameter(client, project_ctx):
    """Test that a parameter can be deleted."""
    project_id = project_ctx["project_id"]
    material_id = client.post(f"/api/projects/{project_id}/materials", json={}).json()["id"]
    param_id = client.post(
        f"/api/projects/{project_id}/materials/{material_id}/parameters",
        json={"domain": "identity", "key": "name", "value_string": "iron_ore"},
    ).json()["id"]
    response = client.delete(
        f"/api/projects/{project_id}/materials/{material_id}/parameters/{param_id}"
    )
    assert response.status_code == 204
