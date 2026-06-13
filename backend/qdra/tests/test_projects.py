def test_create_project(client):
    """Test that a project can be created."""
    response = client.post(
        "/projects",
        json={
            "name": "Factory Test",
            "slug": "factory-test",
            "description": "Example project",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Factory Test"
    assert data["slug"] == "factory-test"
    assert data["description"] == "Example project"
    assert "id" in data


def test_list_projects(client):
    """Test that projects can be listed."""
    # Create a project first
    client.post(
        "/projects",
        json={"name": "Project 1", "slug": "project-1", "description": "First project"},
    )
    client.post(
        "/projects",
        json={"name": "Project 2", "slug": "project-2", "description": "Second project"},
    )

    response = client.get("/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Project 1"
    assert data[1]["name"] == "Project 2"


def test_cannot_create_duplicate_project_slug(client):
    """Test that duplicate project slugs are rejected."""
    client.post(
        "/projects",
        json={"name": "Factory Test", "slug": "factory-test", "description": "Example"},
    )

    response = client.post(
        "/projects",
        json={"name": "Another Factory", "slug": "factory-test", "description": "Duplicate"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
