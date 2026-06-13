def test_create_field_definition_for_object_type(client):
    """Test that a field definition can be created for an object type."""
    # Create a project
    project_response = client.post(
        "/projects",
        json={"name": "Factory Test", "slug": "factory-test", "description": "Example"},
    )
    project_id = project_response.json()["id"]

    # Create an object type
    object_type_response = client.post(
        f"/projects/{project_id}/object-types",
        json={"name": "Material", "description": "A material"},
    )
    object_type_id = object_type_response.json()["id"]

    # Create a field definition
    response = client.post(
        f"/object-types/{object_type_id}/fields",
        json={
            "name": "unit",
            "field_type": "string",
            "required": True,
            "default_value": None,
            "description": "Measurement unit",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "unit"
    assert data["field_type"] == "string"
    assert data["required"] is True
    assert data["description"] == "Measurement unit"
    assert data["object_type_id"] == object_type_id
    assert "id" in data


def test_list_fields_for_object_type(client):
    """Test that fields can be listed for an object type."""
    # Create a project
    project_response = client.post(
        "/projects",
        json={"name": "Factory Test", "slug": "factory-test", "description": "Example"},
    )
    project_id = project_response.json()["id"]

    # Create an object type
    object_type_response = client.post(
        f"/projects/{project_id}/object-types",
        json={"name": "Material", "description": "A material"},
    )
    object_type_id = object_type_response.json()["id"]

    # Create field definitions
    client.post(
        f"/object-types/{object_type_id}/fields",
        json={"name": "unit", "field_type": "string", "required": True},
    )
    client.post(
        f"/object-types/{object_type_id}/fields",
        json={"name": "quantity", "field_type": "number", "required": True},
    )

    # List fields
    response = client.get(f"/object-types/{object_type_id}/fields")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "unit"
    assert data[1]["name"] == "quantity"


def test_cannot_create_field_for_missing_object_type(client):
    """Test that creating a field for a non-existent object type fails."""
    fake_object_type_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/object-types/{fake_object_type_id}/fields",
        json={"name": "unit", "field_type": "string", "required": True},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_cannot_create_duplicate_field_name_in_same_object_type(client):
    """Test that duplicate field names in the same object type are rejected."""
    # Create a project
    project_response = client.post(
        "/projects",
        json={"name": "Factory Test", "slug": "factory-test", "description": "Example"},
    )
    project_id = project_response.json()["id"]

    # Create an object type
    object_type_response = client.post(
        f"/projects/{project_id}/object-types",
        json={"name": "Material", "description": "A material"},
    )
    object_type_id = object_type_response.json()["id"]

    # Create first field
    client.post(
        f"/object-types/{object_type_id}/fields",
        json={"name": "unit", "field_type": "string", "required": True},
    )

    # Try to create duplicate
    response = client.post(
        f"/object-types/{object_type_id}/fields",
        json={"name": "unit", "field_type": "string", "required": False},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_cannot_create_field_with_invalid_field_type(client):
    """Test that invalid field types are rejected."""
    # Create a project
    project_response = client.post(
        "/projects",
        json={"name": "Factory Test", "slug": "factory-test", "description": "Example"},
    )
    project_id = project_response.json()["id"]

    # Create an object type
    object_type_response = client.post(
        f"/projects/{project_id}/object-types",
        json={"name": "Material", "description": "A material"},
    )
    object_type_id = object_type_response.json()["id"]

    # Try to create field with invalid type
    response = client.post(
        f"/object-types/{object_type_id}/fields",
        json={"name": "unit", "field_type": "invalid_type", "required": True},
    )
    assert response.status_code == 422
    assert "Invalid field type" in response.json()["detail"]
