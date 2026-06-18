def test_get_project_template(client, project_ctx):
    """Test that a project's template can be fetched."""
    project_id = project_ctx["project_id"]
    response = client.get(f"/projects/{project_id}/template")
    assert response.status_code == 200
    data = response.json()
    assert "template" in data
    assert "entity_types" in data
    assert "views" in data
    assert data["template"]["id"] == project_ctx["template_id"]


def test_get_entities_by_view_config(client, project_ctx):
    """Test that entities can be filtered by view config."""
    project_id = project_ctx["project_id"]
    template_id = project_ctx["template_id"]
    
    # Create an entity
    response = client.post(
        f"/projects/{project_id}/entities",
        json={"entity_type_id": project_ctx["entity_type_id"]},
    )
    assert response.status_code == 201
    entity = response.json()
    
    # Get view config from template
    template_response = client.get(f"/projects/{project_id}/template")
    template_data = template_response.json()
    material_view = next((v for v in template_data["views"] if v["view_key"] == "material_catalog"), None)
    assert material_view is not None
    assert len(material_view["configs"]) > 0
    config_id = material_view["configs"][0]["id"]
    
    # Get entities by view config
    response = client.get(f"/projects/{project_id}/view-configs/{config_id}/entities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(e["id"] == entity["id"] for e in data)


def test_update_entity_parameters(client, project_ctx):
    """Test that entity parameters can be updated."""
    project_id = project_ctx["project_id"]
    
    # Create an entity
    response = client.post(
        f"/projects/{project_id}/entities",
        json={"entity_type_id": project_ctx["entity_type_id"]},
    )
    assert response.status_code == 201
    entity = response.json()
    entity_id = entity["id"]
    
    # Add a parameter
    client.post(
        f"/projects/{project_id}/entities/{entity_id}/parameters",
        json={"domain": "test", "key": "name", "value_string": "Old Name"},
    )
    
    # Update entity parameters
    response = client.put(
        f"/projects/{project_id}/entities/{entity_id}",
        json={
            "parameters": [
                {"domain": "test", "key": "name", "value_string": "New Name"},
                {"domain": "test", "key": "count", "value_number": 42},
            ]
        },
    )
    assert response.status_code == 200
    
    # Verify parameters were updated
    response = client.get(f"/projects/{project_id}/entities/{entity_id}/parameters")
    assert response.status_code == 200
    params = response.json()
    assert len(params) == 2
    name_param = next((p for p in params if p["key"] == "name"), None)
    assert name_param is not None
    assert name_param["value_string"] == "New Name"
    count_param = next((p for p in params if p["key"] == "count"), None)
    assert count_param is not None
    assert count_param["value_number"] == 42
