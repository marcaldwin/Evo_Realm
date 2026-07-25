from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from backend.app.api.routes import health as health_routes
from backend.app.main import app


client = TestClient(app)


def test_root_endpoint_returns_api_information() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "EvoRealm API",
        "version": "0.1.0",
        "docs": "/docs",
    }


def test_liveness_endpoint_reports_application_is_alive() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_endpoint_reports_application_is_ready(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(health_routes, "is_database_ready", lambda: True)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_endpoint_reports_database_unavailable(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(health_routes, "is_database_ready", lambda: False)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable"}


def test_openapi_schema_contains_metadata_and_api_paths() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"] == {
        "title": "EvoRealm API",
        "description": "Backend API for the EvoRealm simulation",
        "version": "0.1.0",
    }
    assert {"/", "/health/live", "/health/ready"} <= set(schema["paths"])


def test_swagger_documentation_loads() -> None:
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()
