from datetime import datetime, timezone
import json
import re
import uuid
from pathlib import Path
from typing import Any

from hermes_writer.api.errors import ApiError
from hermes_writer.storage.atomic_writer import append_jsonl_atomic, write_json_atomic
from hermes_writer.storage.file_lock import file_lock
from hermes_writer.storage.path_registry import PathRegistry
from hermes_writer.storage.profile_store import ProfileStore

PENDING = "PENDING"
APPROVED = "APPROVED"
ACTIVE = "ACTIVE"
SKILL_STATUSES = {PENDING, APPROVED, ACTIVE}

_SLUG_RE = re.compile(r"[^a-z0-9_-]+")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slugify(value: str) -> str:
    slug = _SLUG_RE.sub("-", value.strip().lower()).strip("-_")
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug:
        raise ApiError("INVALID_REQUEST", "Skill name must contain letters or numbers.")
    return slug[:48]


class SkillStore:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root
        self.registry = PathRegistry(storage_root)
        self.profile_store = ProfileStore(storage_root)

    def create_from_review(
        self,
        *,
        profile_id: str,
        analysis: dict[str, Any],
        review: dict[str, Any],
    ) -> dict[str, Any]:
        self.profile_store.get_profile(profile_id)
        rules = self._skill_rules(review)
        if not rules:
            raise ApiError(
                "NO_APPROVED_RULES",
                "At least one approved, edited, or custom rule is required to create a skill.",
                status_code=422,
            )

        skill_name = str(analysis.get("skill_name") or "Writing Skill").strip()
        skill_id = self._next_skill_id(profile_id, skill_name)
        now = _now_iso()
        skill = {
            "schema_version": 1,
            "skill_id": skill_id,
            "profile_id": profile_id,
            "name": skill_name,
            "lifecycle_status": PENDING,
            "version": 1,
            "created_from_analysis_id": analysis["analysis_id"],
            "rules": rules,
            "created_at": now,
            "updated_at": now,
        }
        metadata = {
            "schema_version": 1,
            "skill_id": skill_id,
            "profile_id": profile_id,
            "name": skill_name,
            "lifecycle_status": PENDING,
            "current_version": 1,
            "default": False,
            "created_from_analysis_id": analysis["analysis_id"],
            "created_at": now,
            "updated_at": now,
            "versions": [
                {
                    "version": 1,
                    "status": PENDING,
                    "created_at": now,
                    "approved_at": None,
                    "activated_at": None,
                    "change_summary": "Created from reviewed rules.",
                    "path": "versions/v1.skill.json",
                }
            ],
        }

        self._write_json_locked(self.registry.skill_version(profile_id, skill_id, 1), skill)
        self._write_json_locked(self.registry.active_skill(profile_id, skill_id), skill)
        self._write_json_locked(self.registry.skill_metadata(profile_id, skill_id), metadata)
        self._append_audit_event(
            profile_id,
            skill_id,
            {
                "timestamp": now,
                "event_type": "skill_created",
                "actor": "system",
                "skill_id": skill_id,
                "version": 1,
                "from_status": None,
                "to_status": PENDING,
            },
        )
        return self.get_skill(profile_id, skill_id)

    def list_skills(self, profile_id: str) -> list[dict[str, Any]]:
        self.profile_store.get_profile(profile_id)
        skills_root = self.registry.profile(profile_id).parent / "skills"
        if not skills_root.exists():
            return []
        skills = []
        for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            metadata_path = skill_dir / "metadata.json"
            if metadata_path.exists():
                skills.append(self._read_metadata_path(metadata_path))
        return skills

    def get_skill(self, profile_id: str, skill_id: str) -> dict[str, Any]:
        self.profile_store.get_profile(profile_id)
        metadata_path = self.registry.skill_metadata(profile_id, skill_id)
        skill_path = self.registry.active_skill(profile_id, skill_id)
        if not metadata_path.exists() or not skill_path.exists():
            raise ApiError("SKILL_NOT_FOUND", "Skill does not exist.", status_code=404)
        return {
            "metadata": self._read_metadata_path(metadata_path),
            "skill": self._read_json_path(skill_path),
        }

    def approve_skill(self, profile_id: str, skill_id: str) -> dict[str, Any]:
        return self._transition(profile_id, skill_id, from_status=PENDING, to_status=APPROVED)

    def activate_skill(self, profile_id: str, skill_id: str) -> dict[str, Any]:
        return self._transition(profile_id, skill_id, from_status=APPROVED, to_status=ACTIVE)

    def set_default_skill(self, profile_id: str, skill_id: str) -> dict[str, Any]:
        detail = self.get_skill(profile_id, skill_id)
        if detail["metadata"]["lifecycle_status"] != ACTIVE:
            raise ApiError(
                "SKILL_NOT_ACTIVE",
                "Only ACTIVE skills can be set as the profile default.",
                status_code=409,
            )
        self.profile_store.update_profile(profile_id, default_skill=skill_id)
        for metadata in self.list_skills(profile_id):
            current_id = metadata["skill_id"]
            metadata["default"] = current_id == skill_id
            metadata["updated_at"] = _now_iso()
            self._write_json_locked(self.registry.skill_metadata(profile_id, current_id), metadata)
        return self.get_skill(profile_id, skill_id)

    def _transition(
        self,
        profile_id: str,
        skill_id: str,
        *,
        from_status: str,
        to_status: str,
    ) -> dict[str, Any]:
        detail = self.get_skill(profile_id, skill_id)
        metadata = detail["metadata"]
        skill = detail["skill"]
        current = metadata.get("lifecycle_status")
        if current != from_status:
            raise ApiError(
                "INVALID_SKILL_TRANSITION",
                f"Skill must be {from_status} before it can become {to_status}.",
                status_code=409,
                details={"current_status": current, "required_status": from_status},
            )

        now = _now_iso()
        metadata["lifecycle_status"] = to_status
        metadata["updated_at"] = now
        version = self._current_version_entry(metadata)
        version["status"] = to_status
        if to_status == APPROVED:
            version["approved_at"] = now
        if to_status == ACTIVE:
            version["activated_at"] = now

        skill["lifecycle_status"] = to_status
        skill["updated_at"] = now

        self._write_json_locked(self.registry.active_skill(profile_id, skill_id), skill)
        self._write_json_locked(self.registry.skill_metadata(profile_id, skill_id), metadata)
        self._append_audit_event(
            profile_id,
            skill_id,
            {
                "timestamp": now,
                "event_type": "skill_approved" if to_status == APPROVED else "skill_activated",
                "actor": "user",
                "skill_id": skill_id,
                "version": metadata["current_version"],
                "from_status": from_status,
                "to_status": to_status,
            },
        )
        return self.get_skill(profile_id, skill_id)

    def _next_skill_id(self, profile_id: str, skill_name: str) -> str:
        base_id = _slugify(skill_name)
        candidate = base_id
        if not self.registry.skill_metadata(profile_id, candidate).exists():
            return candidate
        return f"{base_id[:39]}-{uuid.uuid4().hex[:8]}"

    def _skill_rules(self, review: dict[str, Any]) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for key in ("approved_rules", "edited_rules", "custom_rules"):
            for rule in review.get(key, []):
                merged[str(rule["rule_id"])] = self._skill_rule(rule)
        return list(merged.values())

    @staticmethod
    def _skill_rule(rule: dict[str, Any]) -> dict[str, Any]:
        return {
            "rule_id": rule["rule_id"],
            "category": rule["category"],
            "title": rule["title"],
            "description": rule["description"],
            "examples": rule["examples"],
            "confidence": rule["confidence"],
            "source": rule["source"],
            "evidence": rule["evidence"],
        }

    @staticmethod
    def _current_version_entry(metadata: dict[str, Any]) -> dict[str, Any]:
        current = metadata["current_version"]
        for version in metadata["versions"]:
            if version["version"] == current:
                return version
        raise ApiError("STORAGE_ERROR", "Skill metadata is missing the current version.", status_code=500)

    @staticmethod
    def _read_json_path(path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ApiError("STORAGE_ERROR", "Skill JSON is invalid.", status_code=500) from exc
        if not isinstance(data, dict):
            raise ApiError("STORAGE_ERROR", "Skill JSON is invalid.", status_code=500)
        return data

    def _read_metadata_path(self, path: Path) -> dict[str, Any]:
        data = self._read_json_path(path)
        if data.get("lifecycle_status") not in SKILL_STATUSES or "skill_id" not in data:
            raise ApiError("STORAGE_ERROR", "Skill metadata is invalid.", status_code=500)
        return data

    @staticmethod
    def _write_json_locked(path: Path, data: dict[str, Any]) -> None:
        lock_path = path.with_name(f".{path.name}.lock")
        with file_lock(lock_path):
            write_json_atomic(path, data)

    def _append_audit_event(self, profile_id: str, skill_id: str, event: dict[str, Any]) -> None:
        append_jsonl_atomic(self.registry.audit_log(profile_id, skill_id), event)
