from dataclasses import dataclass
from enum import StrEnum

from hermes_writer.api.errors import ApiError
from hermes_writer.config.privacy_config import PrivacyMode, validate_privacy_mode

OLLAMA_PROVIDER = "ollama"


class OperationType(StrEnum):
    ANALYSIS = "analysis"
    WRITE = "write"
    REWRITE = "rewrite"
    PROVIDER_TEST = "provider_test"


@dataclass(frozen=True)
class PrivacyValidationResult:
    privacy_mode: PrivacyMode
    provider: str
    operation_type: OperationType


def validate_operation(
    *,
    privacy_mode: str | PrivacyMode | None,
    requested_provider: str | None,
    operation_type: str | OperationType,
    provider_available: bool = True,
    fallback_requested: bool = False,
) -> PrivacyValidationResult:
    if privacy_mode is None:
        raise ApiError(
            "PRIVACY_ENFORCEMENT_REQUIRED",
            "Privacy mode must be selected before model operations can run.",
            status_code=400,
            recovery_hint="Select a privacy mode in Settings before continuing.",
        )

    mode = validate_privacy_mode(privacy_mode)
    provider = (requested_provider or "").strip().lower()
    if not provider:
        raise ApiError(
            "PRIVACY_ENFORCEMENT_REQUIRED",
            "A provider must be resolved before model operations can run.",
            status_code=400,
            recovery_hint="Choose an allowed provider for this privacy mode.",
        )

    try:
        operation = OperationType(str(operation_type))
    except ValueError as exc:
        raise ApiError(
            "INVALID_REQUEST",
            "Unsupported LLM operation type.",
            details={"operation_type": str(operation_type)},
        ) from exc

    if mode == PrivacyMode.LOCAL_ONLY:
        if provider != OLLAMA_PROVIDER or fallback_requested:
            raise ApiError(
                "LOCAL_ONLY_PROVIDER_BLOCKED",
                "Local Only mode permits Ollama only and blocks cloud fallback.",
                status_code=403,
                details={"provider": provider, "operation_type": operation.value},
                recovery_hint="Use Ollama locally or change privacy mode explicitly.",
            )
        if not provider_available:
            raise ApiError(
                "PROVIDER_UNAVAILABLE",
                "Ollama is unavailable. Local Only mode prevents cloud fallback.",
                status_code=503,
                details={"provider": OLLAMA_PROVIDER, "operation_type": operation.value},
                recovery_hint="Start Ollama locally, then retry.",
            )

    return PrivacyValidationResult(
        privacy_mode=mode,
        provider=provider,
        operation_type=operation,
    )
