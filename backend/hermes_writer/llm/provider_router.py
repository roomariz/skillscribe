from dataclasses import dataclass

from hermes_writer.api.errors import ApiError
from hermes_writer.config.privacy_config import PrivacyMode, validate_privacy_mode
from hermes_writer.llm.privacy_guard import OLLAMA_PROVIDER, OperationType, validate_operation

HOSTED_PROVIDERS = {"openai", "groq", "gemini", "openrouter", "mistral"}
KNOWN_PROVIDERS = {OLLAMA_PROVIDER, *HOSTED_PROVIDERS}


@dataclass(frozen=True)
class ProviderRoute:
    provider: str
    privacy_mode: PrivacyMode
    operation_type: OperationType
    fallback_allowed: bool


def validate_provider_name(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized not in KNOWN_PROVIDERS:
        raise ApiError(
            "INVALID_REQUEST",
            "Unsupported provider.",
            details={"provider": provider, "supported_providers": sorted(KNOWN_PROVIDERS)},
        )
    return normalized


def allowed_providers(
    privacy_mode: str | PrivacyMode,
    *,
    selected_hosted_providers: set[str] | None = None,
) -> list[str]:
    mode = validate_privacy_mode(privacy_mode)
    selected = {validate_provider_name(provider) for provider in (selected_hosted_providers or set())}
    hosted = sorted(provider for provider in selected if provider in HOSTED_PROVIDERS)

    if mode == PrivacyMode.LOCAL_ONLY:
        return [OLLAMA_PROVIDER]
    if mode == PrivacyMode.HYBRID:
        return [OLLAMA_PROVIDER, *hosted]
    return hosted


def resolve_route(
    *,
    privacy_mode: str | PrivacyMode,
    requested_provider: str,
    operation_type: str | OperationType,
    provider_available: bool,
    selected_hosted_providers: set[str] | None = None,
    fallback_requested: bool = False,
) -> ProviderRoute:
    provider = validate_provider_name(requested_provider)
    mode = validate_privacy_mode(privacy_mode)
    allowed = allowed_providers(mode, selected_hosted_providers=selected_hosted_providers)
    if provider not in allowed:
        if mode == PrivacyMode.LOCAL_ONLY:
            validate_operation(
                privacy_mode=mode,
                requested_provider=provider,
                operation_type=operation_type,
                provider_available=provider_available,
                fallback_requested=fallback_requested,
            )
        raise ApiError(
            "LOCAL_ONLY_PROVIDER_BLOCKED" if mode == PrivacyMode.LOCAL_ONLY else "INVALID_REQUEST",
            "Requested provider is not allowed for the selected privacy mode.",
            status_code=403,
            details={"provider": provider, "privacy_mode": mode.value, "allowed_providers": allowed},
            recovery_hint="Select a provider allowed by the current privacy mode.",
        )

    result = validate_operation(
        privacy_mode=mode,
        requested_provider=provider,
        operation_type=operation_type,
        provider_available=provider_available,
        fallback_requested=fallback_requested,
    )
    return ProviderRoute(
        provider=result.provider,
        privacy_mode=result.privacy_mode,
        operation_type=result.operation_type,
        fallback_allowed=mode != PrivacyMode.LOCAL_ONLY and provider in HOSTED_PROVIDERS,
    )
