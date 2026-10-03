from fastapi.testclient import TestClient

from server.main import app


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_health_cors() -> None:
    client = TestClient(app)
    for origin in ("http://127.0.0.1:5173", "http://localhost:4173", "null"):
        response = client.get("/health", headers={"Origin": origin})
        assert response.headers["access-control-allow-origin"] == origin
    response = client.get("/health", headers={"Origin": "https://example.com"})
    assert "access-control-allow-origin" not in response.headers
