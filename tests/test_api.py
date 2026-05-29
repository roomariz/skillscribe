from fastapi.testclient import TestClient
import pytest

from hermes_writer.api.app import create_app
from hermes_writer.api.errors import ApiError
from hermes_writer.config.settings import Settings


def test_health_returns_ok_and_initializes_storage(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["storage_available"] is True
    assert body["profiles_count"] == 0


def test_status_uses_api_envelope(client):
    response = client.get("/api/status")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["database_type"] == "file-based"
    assert body["data"]["privacy_mode"] == "local_only"
    assert "timestamp" in body


def test_version_endpoint(client):
    response = client.get("/api/version")

    assert response.status_code == 200
    assert response.json()["data"] == {"version": "1.0.0"}


def test_cors_allows_localhost_5173(client):
    response = client.options(
        "/api/status",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_unapproved_origin(client):
    response = client.options(
        "/api/status",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_unknown_api_route_uses_error_envelope(client):
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "NOT_FOUND"
    assert body["message"]
    assert "timestamp" in body


def test_method_not_allowed_uses_error_envelope(client):
    response = client.post("/api/status")

    assert response.status_code == 405
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "METHOD_NOT_ALLOWED"
    assert body["message"]
    assert "timestamp" in body


def test_config_validation_runs_on_startup(tmp_path):
    settings = Settings(
        storage_root=tmp_path / "data",
        cors_origin="http://localhost:5173",
        log_level="INFO",
        privacy_mode="local_only",
        litellm_base_url="",
        ollama_base_url="",
    )

    app = create_app(settings)
    with TestClient(app) as test_client:
        response = test_client.get("/api/status")

    assert response.status_code == 200
    assert (tmp_path / "data" / ".version").exists()


def test_missing_required_config_fails_startup_with_recovery_hint(tmp_path):
    settings = Settings(
        storage_root=tmp_path / "data",
        cors_origin="",
        log_level="INFO",
        privacy_mode="local_only",
        litellm_base_url="",
        ollama_base_url="",
    )

    app = create_app(settings)
    with pytest.raises(ApiError) as exc_info, TestClient(app):
        pass

    error = exc_info.value
    assert error.error_code == "CONFIG_MISSING"
    assert error.details == {"missing": ["HERMES_WRITER_CORS_ORIGIN"]}
    assert error.recovery_hint == "Set required setting(s): HERMES_WRITER_CORS_ORIGIN."
