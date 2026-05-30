from unittest.mock import patch

from hermes_writer.llm.litellm_client import ProviderConnection
from hermes_writer.llm.provider_detection import ProviderStatus


def test_update_privacy_mode_endpoint(client):
    response = client.post("/api/config/update-privacy-mode", json={"privacy_mode": "hybrid"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["privacy_mode"] == "hybrid"

    status = client.get("/api/status")
    assert status.json()["data"]["privacy_mode"] == "hybrid"


def test_provider_test_endpoint(client):
    statuses = [
        ProviderStatus(name="ollama", available=True, configured=True, model="ollama"),
        ProviderStatus(name="groq", available=False, configured=False),
    ]
    with (
        patch("hermes_writer.api.routes.config.detect_providers", return_value=statuses),
        patch(
            "hermes_writer.api.routes.config.LiteLLMClient.test_connection",
            return_value=ProviderConnection(provider="ollama", connected=True, model="ollama/mistral"),
        ) as test_connection,
    ):
        response = client.post("/api/config/test-provider", json={"provider": "ollama"})

    assert response.status_code == 200
    assert response.json()["data"] == {
        "provider": "ollama",
        "connected": True,
        "model": "ollama/mistral",
    }
    test_connection.assert_called_once_with("ollama")


def test_config_endpoint_returns_expected_structure(client):
    statuses = [
        ProviderStatus(name="ollama", available=False, configured=True, model="ollama"),
        ProviderStatus(name="openai", available=True, configured=True),
    ]
    with patch("hermes_writer.api.routes.config.detect_providers", return_value=statuses):
        response = client.get("/api/config")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["privacy_mode"] == "local_only"
    assert body["data"]["max_upload_size_mb"] == 50
    assert body["data"]["storage_path"]
    assert body["data"]["providers"] == [
        {"name": "ollama", "available": False, "configured": True, "model": "ollama"},
        {"name": "openai", "available": True, "configured": True, "model": None},
    ]


def test_provider_test_rejects_cloud_provider_in_local_only(client):
    statuses = [
        ProviderStatus(name="ollama", available=True, configured=True, model="ollama"),
        ProviderStatus(name="openai", available=True, configured=True),
    ]
    with patch("hermes_writer.api.routes.config.detect_providers", return_value=statuses):
        response = client.post("/api/config/test-provider", json={"provider": "openai"})

    assert response.status_code == 403
    assert response.json()["error_code"] == "LOCAL_ONLY_PROVIDER_BLOCKED"
