def test_create_object_type_inside_project(client):
    """Test that an object type can be created inside a project."""
    # Create a project first
    project_response = client.post(
        "/projects",
        json={"name": "Factory Test", "slug": "factory-test", "description": "Example"},
    )
    project_id = project_response.json()["id"]

    # Create an object type
    response = client.post(
        f"/projects/{project_id}/object-types",
        json={"name": "Material", "description": "A material that can be consumed or produced"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Material"
    assert data["description"] == "A material that can be consumed or produced"
    assert data["project_id"] == project_id
    assert "id" in data


def test_list_object_types_for_project(client):
    """Test that object types can be listed for a project."""
    # Create a project
    project_response = client.post(
        "/projects",
        json={"name": "Factory Test", "slug": "factory-test", "description": "Example"},
    )
    project_id = project_response.json()["id"]

    # Create object types
    client.post(
        f"/projects/{project_id}/object-types",
        json={"name": "Material", "description": "A material"},
    )
    client.post(
        f"/projects/{project_id}/object-types",
        json={"name": "Machine", "description": "A machine"},
    )

    # List object types
    response = client.get(f"/projects/{project_id}/object-types")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Material"
    assert data[1]["name"] == "Machine"


def test_cannot_create_object_type_for_missing_project(client):
    """Test that creating an object type for a non-existent project fails."""
    fake_project_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/projects/{fake_project_id}/object-types",
        json={"name": "Material", "description": "A material"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_cannot_create_duplicate_object_type_name_in_same_project(client):
    """Test that duplicate object type names in the same project are rejected."""
    # Create a project
    project_response = client.post(
        "/projects",
        json={"name": "Factory Test", "slug": "factory-test", "description": "Example"},
    )
    project_id = project_response.json()["id"]

    # Create first object type
    client.post(
        f"/projects/{project_id}/object-types",
        json={"name": "Material", "description": "A material"},
    )

    # Try to create duplicate
    response = client.post(
        f"/projects/{project_id}/object-types",
        json={"name": "Material", "description": "Another material"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_can_create_same_object_type_name_in_different_projects(client):
    """Test that the same object type name can be used in different projects."""
    # Create two projects
    project1_response = client.post(
        "/projects",
        json={"name": "Factory 1", "slug": "factory-1", "description": "First factory"},
    )
    project1_id = project1_response.json()["id"]

    project2_response = client.post(
        "/projects",
        json={"name": "Factory 2", "slug": "factory-2", "description": "Second factory"},
    )
    project2_id = project2_response.json()["id"]

    # Create object type with same name in both projects
    response1 = client.post(
        f"/projects/{project1_id}/object-types",
        json={"name": "Material", "description": "A material"},
    )
    assert response1.status_code == 201

    response2 = client.post(
        f"/projects/{project2_id}/object-types",
        json={"name": "Material", "description": "A material"},
    )
    assert response2.status_code == 201
