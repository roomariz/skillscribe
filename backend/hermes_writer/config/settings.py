from dataclasses import dataclass
import os
from pathlib import Path

from hermes_writer.api.errors import ApiError
from hermes_writer.config.privacy_config import PrivacyMode, validate_privacy_mode


@dataclass(frozen=True)
class Settings:
    storage_root: Path
    cors_origin: str
    log_level: str
    privacy_mode: str
    litellm_base_url: str
    ollama_base_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            storage_root=Path(os.getenv("HERMES_WRITER_STORAGE_ROOT", "./data")),
            cors_origin=os.getenv("HERMES_WRITER_CORS_ORIGIN", "http://localhost:5173"),
            log_level=os.getenv("HERMES_WRITER_LOG_LEVEL", "INFO"),
            privacy_mode=os.getenv("HERMES_WRITER_PRIVACY_MODE", "local_only"),
            litellm_base_url=os.getenv("LITELLM_BASE_URL", "http://localhost:4000"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

    def validate(self) -> list[str]:
        missing: list[str] = []
        if not str(self.storage_root):
            missing.append("HERMES_WRITER_STORAGE_ROOT")
        if not self.cors_origin:
            missing.append("HERMES_WRITER_CORS_ORIGIN")
        if not self.log_level:
            missing.append("HERMES_WRITER_LOG_LEVEL")
        if not self.privacy_mode:
            missing.append("HERMES_WRITER_PRIVACY_MODE")
        try:
            validate_privacy_mode(self.privacy_mode)
        except ApiError:
            missing.append("HERMES_WRITER_PRIVACY_MODE")
        return missing

    @property
    def default_privacy_mode(self) -> PrivacyMode:
        return validate_privacy_mode(self.privacy_mode)

    def validate_for_startup(self) -> None:
        missing = sorted(set(self.validate()))
        if missing:
            missing_list = ", ".join(missing)
            raise ApiError(
                "CONFIG_MISSING",
                "Required startup configuration is missing or invalid.",
                status_code=500,
                details={"missing": missing},
                recovery_hint=f"Set required setting(s): {missing_list}.",
            )
