"""Tests for project template entity types and parameter definitions endpoints."""


def test_list_entity_types(client, project_ctx):
    """Test listing entity types for a template."""
    template_id = project_ctx["template_id"]
    response = client.get(f"/project-templates/{template_id}/entity-types")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    kinds = {et["kind"] for et in data}
    assert "material" in kinds
    assert "recipe" in kinds


def test_list_entity_types_by_kind(client, project_ctx):
    """Test filtering entity types by kind."""
    template_id = project_ctx["template_id"]
    response = client.get(f"/project-templates/{template_id}/entity-types?kind=material")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["kind"] == "material"


def test_get_entity_type(client, project_ctx):
    """Test getting a single entity type."""
    template_id = project_ctx["template_id"]
    material_type_id = project_ctx["material_type_id"]
    response = client.get(f"/project-templates/{template_id}/entity-types/{material_type_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == material_type_id
    assert data["kind"] == "material"
    assert "parameter_definitions" in data


def test_create_entity_type_material(client, project_ctx):
    """Test creating a material entity type."""
    template_id = project_ctx["template_id"]
    response = client.post(
        f"/project-templates/{template_id}/entity-types",
        json={"kind": "material", "name": "Item", "description": "A craftable item"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "material"
    assert data["name"] == "Item"
    assert data["description"] == "A craftable item"
    assert data["parameter_definitions"] == []


def test_create_entity_type_recipe(client, project_ctx):
    """Test creating a recipe entity type."""
    template_id = project_ctx["template_id"]
    response = client.post(
        f"/project-templates/{template_id}/entity-types",
        json={"kind": "recipe", "name": "Crafting Recipe"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "recipe"
    assert data["name"] == "Crafting Recipe"


def test_create_entity_type_invalid_kind(client, project_ctx):
    """Test that creating an entity type with invalid kind fails."""
    template_id = project_ctx["project_template_id"]
    response = client.post(
        f"/project-templates/{template_id}/entity-types",
        json={"kind": "invalid", "name": "Test"},
    )
    assert response.status_code == 400


def test_create_entity_type_missing_name(client, project_ctx):
    """Test that creating an entity type without name fails."""
    template_id = project_ctx["template_id"]
    response = client.post(
        f"/project-templates/{template_id}/entity-types",
        json={"kind": "material"},
    )
    assert response.status_code == 422


def test_update_entity_type(client, project_ctx):
    """Test updating an entity type."""
    template_id = project_ctx["template_id"]
    material_type_id = project_ctx["material_type_id"]
    response = client.put(
        f"/project-templates/{template_id}/entity-types/{material_type_id}",
        json={"name": "Updated Material", "description": "Updated description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Material"
    assert data["description"] == "Updated description"


def test_update_entity_type_not_found(client, project_ctx):
    """Test updating a non-existent entity type."""
    template_id = project_ctx["template_id"]
    import uuid
    fake_id = uuid.uuid4()
    response = client.put(
        f"/project-templates/{template_id}/entity-types/{fake_id}",
        json={"name": "Test"},
    )
    assert response.status_code == 404


def test_delete_entity_type_unused(client, project_ctx):
    """Test deleting an unused entity type."""
    template_id = project_ctx["template_id"]
    # Create a new entity type
    new_type = client.post(
        f"/project-templates/{template_id}/entity-types",
        json={"kind": "material", "name": "Temporary"},
    ).json()
    response = client.delete(f"/project-templates/{template_id}/entity-types/{new_type['id']}")
    assert response.status_code == 204


def test_delete_entity_type_used_by_entities(client, project_ctx):
    """Test that deleting an entity type used by entities fails."""
    template_id = project_ctx["template_id"]
    material_type_id = project_ctx["material_type_id"]
    project_id = project_ctx["project_id"]
    
    # Create an entity using the material type
    client.post(
        f"/projects/{project_id}/entities",
        json={"entity_type_id": material_type_id},
    )
    
    # Try to delete the entity type
    response = client.delete(f"/project-templates/{template_id}/entity-types/{material_type_id}")
    assert response.status_code == 409


def test_clone_entity_type(client, project_ctx):
    """Test cloning an entity type."""
    template_id = project_ctx["template_id"]
    material_type_id = project_ctx["material_type_id"]
    response = client.post(f"/project-templates/{template_id}/entity-types/{material_type_id}/clone")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Material Copy"
    assert data["kind"] == "material"


def test_list_parameter_definitions(client, project_ctx):
    """Test listing parameter definitions for an entity type."""
    template_id = project_ctx["template_id"]
    material_type_id = project_ctx["material_type_id"]
    response = client.get(
        f"/project-templates/{template_id}/entity-types/{material_type_id}/parameter-definitions"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_parameter_definition(client, project_ctx):
    """Test creating a parameter definition."""
    template_id = project_ctx["template_id"]
    material_type_id = project_ctx["material_type_id"]
    response = client.post(
        f"/project-templates/{template_id}/entity-types/{material_type_id}/parameter-definitions",
        json={
            "domain": "identity",
            "key": "name",
            "value_type": "string",
            "label": "Name",
            "required": True,
            "is_label": True,
            "is_unique": True,
            "is_searchable": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "identity"
    assert data["key"] == "name"
    assert data["value_type"] == "string"
    assert data["label"] == "Name"
    assert data["required"] is True


def test_create_parameter_definition_invalid_value_type(client, project_ctx):
    """Test that creating a parameter definition with invalid value_type fails."""
    template_id = project_ctx["template_id"]
    material_type_id = project_ctx["material_type_id"]
    response = client.post(
        f"/project-templates/{template_id}/entity-types/{material_type_id}/parameter-definitions",
        json={"domain": "identity", "key": "test", "value_type": "invalid"},
    )
    assert response.status_code == 400


def test_update_parameter_definition(client, project_ctx):
    """Test updating a parameter definition."""
    template_id = project_ctx["template_id"]
    material_type_id = project_ctx["material_type_id"]
    
    # First create a parameter definition
    param = client.post(
        f"/project-templates/{template_id}/entity-types/{material_type_id}/parameter-definitions",
        json={"domain": "identity", "key": "test", "value_type": "string", "label": "Test"},
    ).json()
    
    # Update it
    response = client.patch(
        f"/project-templates/{template_id}/entity-types/{material_type_id}/parameter-definitions/{param['id']}",
        json={"label": "Updated Label", "required": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "Updated Label"
    assert data["required"] is True


def test_delete_parameter_definition(client, project_ctx):
    """Test deleting a parameter definition."""
    template_id = project_ctx["template_id"]
    material_type_id = project_ctx["material_type_id"]
    
    # First create a parameter definition
    param = client.post(
        f"/project-templates/{template_id}/entity-types/{material_type_id}/parameter-definitions",
        json={"domain": "identity", "key": "test", "value_type": "string", "label": "Test"},
    ).json()
    
    # Delete it
    response = client.delete(
        f"/project-templates/{template_id}/entity-types/{material_type_id}/parameter-definitions/{param['id']}"
    )
    assert response.status_code == 204
