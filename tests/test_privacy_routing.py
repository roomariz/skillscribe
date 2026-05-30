import pytest

from hermes_writer.api.errors import ApiError
from hermes_writer.config.privacy_config import PrivacyConfigStore, PrivacyMode, validate_privacy_mode
from hermes_writer.llm.privacy_guard import validate_operation
from hermes_writer.llm.provider_router import allowed_providers, resolve_route


def test_local_only_allows_ollama_only():
    route = resolve_route(
        privacy_mode=PrivacyMode.LOCAL_ONLY,
        requested_provider="ollama",
        operation_type="analysis",
        provider_available=True,
    )

    assert route.provider == "ollama"
    assert allowed_providers(PrivacyMode.LOCAL_ONLY) == ["ollama"]


def test_local_only_rejects_cloud_provider():
    with pytest.raises(ApiError) as exc_info:
        resolve_route(
            privacy_mode=PrivacyMode.LOCAL_ONLY,
            requested_provider="openai",
            operation_type="analysis",
            provider_available=True,
        )

    assert exc_info.value.error_code == "LOCAL_ONLY_PROVIDER_BLOCKED"


def test_local_only_fails_closed_when_ollama_unavailable():
    with pytest.raises(ApiError) as exc_info:
        resolve_route(
            privacy_mode=PrivacyMode.LOCAL_ONLY,
            requested_provider="ollama",
            operation_type="analysis",
            provider_available=False,
        )

    assert exc_info.value.error_code == "PROVIDER_UNAVAILABLE"


def test_hybrid_allows_user_selected_fallback():
    route = resolve_route(
        privacy_mode=PrivacyMode.HYBRID,
        requested_provider="groq",
        operation_type="analysis",
        provider_available=True,
        selected_hosted_providers={"groq"},
        fallback_requested=True,
    )

    assert route.provider == "groq"
    assert route.fallback_allowed is True


def test_cloud_allowed_permits_selected_provider():
    route = resolve_route(
        privacy_mode=PrivacyMode.CLOUD_ALLOWED,
        requested_provider="mistral",
        operation_type="provider_test",
        provider_available=True,
        selected_hosted_providers={"mistral"},
    )

    assert route.provider == "mistral"


def test_privacy_guard_blocks_invalid_route():
    with pytest.raises(ApiError) as exc_info:
        validate_operation(
            privacy_mode=None,
            requested_provider="ollama",
            operation_type="analysis",
        )

    assert exc_info.value.error_code == "PRIVACY_ENFORCEMENT_REQUIRED"


def test_privacy_config_persists_mode(tmp_path):
    store = PrivacyConfigStore(tmp_path)

    assert store.get_mode() == PrivacyMode.LOCAL_ONLY
    assert store.set_mode("hybrid") == PrivacyMode.HYBRID
    assert PrivacyConfigStore(tmp_path).get_mode() == PrivacyMode.HYBRID


def test_validate_privacy_mode_rejects_unknown_value():
    with pytest.raises(ApiError):
        validate_privacy_mode("cloud_only")
