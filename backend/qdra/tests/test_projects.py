def test_create_project(client, project_ctx):
    """Test that a project can be created."""
    template_id = project_ctx["template_id"]
    response = client.post(
        "/projects",
        json={"name": "Factory Test", "project_template_id": template_id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Factory Test"
    assert "id" in data


def test_list_projects(client, project_ctx):
    """Test that projects can be listed."""
    template_id = project_ctx["template_id"]
    client.post("/api/projects", json={"name": "Project 1", "project_template_id": template_id})
    client.post("/api/projects", json={"name": "Project 2", "project_template_id": template_id})
    response = client.get("/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_cannot_create_project_without_template(client):
    """Test that creating a project without a template fails."""
    response = client.post("/api/projects", json={"name": "No Template"})
    assert response.status_code == 422
