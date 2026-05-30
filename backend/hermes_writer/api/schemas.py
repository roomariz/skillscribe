from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SuccessEnvelope(BaseModel):
    success: bool = True
    data: Any
    timestamp: datetime = Field(default_factory=utc_now)


class ErrorEnvelope(BaseModel):
    success: bool = False
    error_code: str
    message: str
    timestamp: datetime = Field(default_factory=utc_now)
    details: dict[str, Any] | None = None
    recovery_hint: str | None = None

    @classmethod
    def from_error(
        cls,
        *,
        error_code: str,
        message: str,
        details: dict[str, Any] | None = None,
        recovery_hint: str | None = None,
    ) -> "ErrorEnvelope":
        return cls(
            error_code=error_code,
            message=message,
            details=details,
            recovery_hint=recovery_hint,
        )


class ProfileCreateRequest(BaseModel):
    profile_id: str | None = None
    display_name: str
    description: str = ""


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = None
    description: str | None = None
    default_skill: str | None = None


class ExtractedTextUpdateRequest(BaseModel):
    extracted_text: str


class PrivacyModeUpdateRequest(BaseModel):
    privacy_mode: str


class ProviderTestRequest(BaseModel):
    provider: str


class AnalyzeStyleRequest(BaseModel):
    document_ids: list[str]
    skill_name: str
    provider: str | None = None
