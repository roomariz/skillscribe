from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path
from typing import Any

from hermes_writer.api.errors import ApiError
from hermes_writer.storage.atomic_writer import write_text_atomic


class PrivacyMode(StrEnum):
    LOCAL_ONLY = "local_only"
    HYBRID = "hybrid"
    CLOUD_ALLOWED = "cloud_allowed"


DEFAULT_PRIVACY_MODE = PrivacyMode.LOCAL_ONLY


def validate_privacy_mode(value: str | PrivacyMode) -> PrivacyMode:
    try:
        return PrivacyMode(str(value))
    except ValueError as exc:
        raise ApiError(
            "INVALID_REQUEST",
            "Privacy mode must be one of: local_only, hybrid, cloud_allowed.",
            details={"privacy_mode": value},
            recovery_hint="Choose Local Only, Hybrid, or Cloud Allowed.",
        ) from exc


@dataclass
class PrivacyConfigStore:
    storage_root: Path
    default_mode: PrivacyMode = DEFAULT_PRIVACY_MODE

    @property
    def config_path(self) -> Path:
        return self.storage_root / "config.json"

    def get_mode(self) -> PrivacyMode:
        if not self.config_path.exists():
            return self.default_mode
        try:
            payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self.default_mode
        return validate_privacy_mode(payload.get("privacy_mode", self.default_mode.value))

    def set_mode(self, privacy_mode: str | PrivacyMode) -> PrivacyMode:
        mode = validate_privacy_mode(privacy_mode)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {"privacy_mode": mode.value}
        write_text_atomic(self.config_path, json.dumps(payload, indent=2) + "\n")
        return mode
