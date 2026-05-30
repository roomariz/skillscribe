from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any

from hermes_writer.api.errors import ApiError
from hermes_writer.storage.atomic_writer import write_json_atomic
from hermes_writer.storage.file_store import LocalFileStore
from hermes_writer.storage.path_registry import PathRegistry

_SLUG_RE = re.compile(r"[^a-z0-9_-]+")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slugify(value: str) -> str:
    slug = _SLUG_RE.sub("-", value.strip().lower()).strip("-_")
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug:
        raise ApiError("INVALID_REQUEST", "Profile name must contain letters or numbers.")
    return slug[:64]


class ProfileStore:
    def __init__(self, storage_root: Path) -> None:
        self.file_store = LocalFileStore(storage_root)
        self.registry = PathRegistry(storage_root)

    def initialize(self) -> None:
        self.file_store.initialize()

    def count_profiles(self) -> int:
        return len(self.list_profiles())

    def create_profile(
        self,
        *,
        display_name: str,
        profile_id: str | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        clean_name = display_name.strip()
        if not clean_name:
            raise ApiError("INVALID_REQUEST", "Profile display name is required.")
        candidate_id = profile_id.strip().lower() if profile_id else _slugify(clean_name)
        path = self.registry.profile(candidate_id)
        if path.exists():
            raise ApiError(
                "PROFILE_EXISTS",
                "A profile with this ID already exists.",
                status_code=409,
            )

        now = _now_iso()
        profile: dict[str, Any] = {
            "profile_id": candidate_id,
            "display_name": clean_name,
            "description": description.strip(),
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
            "default_skill": None,
            "metadata": {
                "total_documents": 0,
                "total_skills": 0,
            },
        }
        self._ensure_profile_dirs(candidate_id)
        write_json_atomic(path, profile)
        return profile

    def list_profiles(self, *, include_deleted: bool = False) -> list[dict[str, Any]]:
        profiles: list[dict[str, Any]] = []
        if not self.file_store.profiles_root.exists():
            return profiles
        for profile_dir in sorted(self.file_store.profiles_root.iterdir()):
            if not profile_dir.is_dir():
                continue
            profile_path = profile_dir / "profile.json"
            if not profile_path.exists():
                continue
            profile = self._read_profile_path(profile_path)
            if profile.get("deleted_at") and not include_deleted:
                continue
            profiles.append(self._with_counts(profile))
        return profiles

    def get_profile(self, profile_id: str, *, include_deleted: bool = False) -> dict[str, Any]:
        profile = self._read_profile(profile_id)
        if profile.get("deleted_at") and not include_deleted:
            raise ApiError("PROFILE_NOT_FOUND", "Profile does not exist.", status_code=404)
        return self._with_counts(profile)

    def update_profile(
        self,
        profile_id: str,
        *,
        display_name: str | None = None,
        description: str | None = None,
        default_skill: str | None = None,
    ) -> dict[str, Any]:
        profile = self.get_profile(profile_id)
        if display_name is not None:
            clean_name = display_name.strip()
            if not clean_name:
                raise ApiError("INVALID_REQUEST", "Profile display name is required.")
            profile["display_name"] = clean_name
        if description is not None:
            profile["description"] = description.strip()
        if default_skill is not None:
            profile["default_skill"] = default_skill.strip() or None
        profile["updated_at"] = _now_iso()
        write_json_atomic(self.registry.profile(profile_id), profile)
        return self._with_counts(profile)

    def soft_delete_profile(self, profile_id: str) -> None:
        profile = self.get_profile(profile_id)
        profile["deleted_at"] = _now_iso()
        profile["updated_at"] = profile["deleted_at"]
        write_json_atomic(self.registry.profile(profile_id), profile)

    def _read_profile(self, profile_id: str) -> dict[str, Any]:
        path = self.registry.profile(profile_id)
        if not path.exists():
            raise ApiError("PROFILE_NOT_FOUND", "Profile does not exist.", status_code=404)
        return self._read_profile_path(path)

    @staticmethod
    def _read_profile_path(path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ApiError(
                "STORAGE_ERROR",
                "Profile metadata is not valid JSON.",
                status_code=500,
            ) from exc
        if not isinstance(data, dict) or "profile_id" not in data:
            raise ApiError("STORAGE_ERROR", "Profile metadata is invalid.", status_code=500)
        return data

    def _ensure_profile_dirs(self, profile_id: str) -> None:
        profile_root = self.registry.profile(profile_id).parent
        for relative in (
            "documents/original",
            "documents/extracted",
            "documents/metadata",
            "skills",
        ):
            (profile_root / relative).mkdir(parents=True, exist_ok=True)

    def _with_counts(self, profile: dict[str, Any]) -> dict[str, Any]:
        profile = dict(profile)
        profile_id = str(profile["profile_id"])
        profile_root = self.registry.profile(profile_id).parent
        documents_dir = profile_root / "documents" / "metadata"
        skills_dir = profile_root / "skills"
        document_count = (
            sum(1 for path in documents_dir.glob("*.json") if path.is_file())
            if documents_dir.exists()
            else 0
        )
        skill_count = (
            sum(1 for path in skills_dir.iterdir() if path.is_dir()) if skills_dir.exists() else 0
        )
        profile["metadata"] = {
            **dict(profile.get("metadata") or {}),
            "total_documents": document_count,
            "total_skills": skill_count,
        }
        profile["document_count"] = document_count
        profile["skill_count"] = skill_count
        return profile
