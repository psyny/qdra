def test_export_import_template(client, db):
    """Test that a template can be exported and imported."""
    # Create a template with some data
    template_response = client.post("/api/project-templates", json={"name": "Test Template", "description": "Test description"})
    assert template_response.status_code == 201
    template_id = template_response.json()["id"]

    # Add an entity type
    et_response = client.post(
        f"/api/project-templates/{template_id}/entity-types",
        json={"kind": "material", "name": "Test Material", "description": "A test material type", "sort_order": 0}
    )
    assert et_response.status_code == 201
    entity_type_id = et_response.json()["id"]

    # Add a parameter definition
    param_response = client.post(
        f"/api/project-templates/{template_id}/entity-types/{entity_type_id}/parameter-definitions",
        json={
            "domain": "identity",
            "key": "name",
            "value_type": "string",
            "label": "Name",
            "description": "Material name",
            "required": True,
            "sort_order": 0,
            "is_label": True,
            "is_unique": True,
            "is_searchable": True,
            "is_hidden": False,
        }
    )
    assert param_response.status_code == 201

    # Add a view
    view_response = client.post(
        f"/api/project-templates/{template_id}/views",
        json={"view_key": "test_view", "label": "Test View", "description": "A test view", "sort_order": 0}
    )
    assert view_response.status_code == 201
    view_id = view_response.json()["id"]

    # Add a view config
    config_response = client.post(
        f"/api/project-templates/{template_id}/views/{view_id}/configs",
        json={
            "entity_type_id": entity_type_id,
            "filter_params": [],
            "display_slots": [],
            "sort_order": 0
        }
    )
    assert config_response.status_code == 201

    # Export the template
    export_response = client.get(f"/api/project-templates/{template_id}/export")
    assert export_response.status_code == 200
    export_data = export_response.json()["data"]

    # Verify export structure
    assert "template" in export_data
    assert "entity_types" in export_data
    assert "views" in export_data
    assert export_data["template"]["name"] == "Test Template"
    assert export_data["template"]["description"] == "Test description"
    assert len(export_data["entity_types"]) == 1
    assert export_data["entity_types"][0]["name"] == "Test Material"
    assert export_data["entity_types"][0]["kind"] == "material"
    assert len(export_data["entity_types"][0]["parameter_definitions"]) == 1
    assert export_data["entity_types"][0]["parameter_definitions"][0]["key"] == "name"
    assert len(export_data["views"]) == 1
    assert export_data["views"][0]["view_key"] == "test_view"
    assert len(export_data["views"][0]["configs"]) == 1

    # Import the template
    import_response = client.post("/api/project-templates/import", json={"data": export_data})
    assert import_response.status_code == 201
    imported_template = import_response.json()
    assert imported_template["name"] == "Test Template"
    assert imported_template["description"] == "Test description"
    imported_template_id = imported_template["id"]

    # Verify the imported template has the same structure
    # Check entity types
    et_list_response = client.get(f"/api/project-templates/{imported_template_id}/entity-types")
    assert et_list_response.status_code == 200
    imported_entity_types = et_list_response.json()
    assert len(imported_entity_types) == 1
    assert imported_entity_types[0]["name"] == "Test Material"
    assert imported_entity_types[0]["kind"] == "material"
    imported_et_id = imported_entity_types[0]["id"]

    # Check parameter definitions
    param_list_response = client.get(
        f"/api/project-templates/{imported_template_id}/entity-types/{imported_et_id}/parameter-definitions"
    )
    assert param_list_response.status_code == 200
    imported_params = param_list_response.json()
    assert len(imported_params) == 1
    assert imported_params[0]["key"] == "name"
    assert imported_params[0]["domain"] == "identity"
    assert imported_params[0]["value_type"] == "string"

    # Check views
    views_list_response = client.get(f"/api/project-templates/{imported_template_id}/views")
    assert views_list_response.status_code == 200
    imported_views = views_list_response.json()
    assert len(imported_views) == 1
    assert imported_views[0]["view_key"] == "test_view"
    assert imported_views[0]["label"] == "Test View"
    assert len(imported_views[0]["configs"]) == 1
