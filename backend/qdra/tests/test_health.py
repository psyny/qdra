def test_health_returns_200(client):
    """Test that GET /health returns 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok_status(client):
    """Test that GET /health returns {'status': 'ok'}."""
    response = client.get("/health")
    assert response.json() == {"status": "ok"}
