def test_export_import_template(client, db):
    """Test that a template can be exported and imported with full slot system and plan output solver."""
    # Create a template with some data
    template_response = client.post("/api/project-templates", json={"name": "Test Template", "description": "Test description"})
    assert template_response.status_code == 201
    template_id = template_response.json()["id"]

    # Add a recipe entity type (to test slot system)
    et_response = client.post(
        f"/api/project-templates/{template_id}/entity-types",
        json={"kind": "recipe", "name": "Test Recipe", "description": "A test recipe type", "sort_order": 0}
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
            "description": "Recipe name",
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

    # Add plan output solver configuration
    plan_output_response = client.post(
        f"/api/project-templates/{template_id}/plan-output-solver",
        json={
            "new_plan_defaults": {"solver_type": "test"},
            "results_view_defaults": {"view_mode": "detailed"}
        }
    )
    assert plan_output_response.status_code == 201

    # Export the template
    export_response = client.get(f"/api/project-templates/{template_id}/export")
    assert export_response.status_code == 200
    export_data = export_response.json()["data"]

    # Verify export structure
    assert "template" in export_data
    assert "entity_types" in export_data
    assert "views" in export_data
    assert "plan_output_solver" in export_data
    assert export_data["template"]["name"] == "Test Template"
    assert export_data["template"]["description"] == "Test description"
    assert len(export_data["entity_types"]) == 1
    assert export_data["entity_types"][0]["name"] == "Test Recipe"
    assert export_data["entity_types"][0]["kind"] == "recipe"
    assert len(export_data["entity_types"][0]["parameter_definitions"]) == 1
    assert export_data["entity_types"][0]["parameter_definitions"][0]["key"] == "name"
    # Verify slot groups are exported (auto-created for recipe entity types)
    assert len(export_data["entity_types"][0]["slot_groups"]) == 3  # consumes, requires, produces
    assert len(export_data["views"]) == 1
    assert export_data["views"][0]["view_key"] == "test_view"
    assert len(export_data["views"][0]["configs"]) == 1
    # Verify plan output solver is exported
    assert export_data["plan_output_solver"] is not None
    assert export_data["plan_output_solver"]["new_plan_defaults"]["solver_type"] == "test"
    assert export_data["plan_output_solver"]["results_view_defaults"]["view_mode"] == "detailed"

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
    assert imported_entity_types[0]["name"] == "Test Recipe"
    assert imported_entity_types[0]["kind"] == "recipe"
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

    # Check plan output solver was imported
    plan_output_get_response = client.get(f"/api/project-templates/{imported_template_id}/plan-output-solver")
    assert plan_output_get_response.status_code == 200
    imported_plan_output = plan_output_get_response.json()
    assert imported_plan_output["new_plan_defaults"]["solver_type"] == "test"
    assert imported_plan_output["results_view_defaults"]["view_mode"] == "detailed"
