import re
from pathlib import Path

from hermes_writer.api.errors import ApiError

_SEGMENT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,127}$")


class PathRegistry:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root

    def profile(self, profile_id: str) -> Path:
        return self._safe_join("profiles", self._segment(profile_id), "profile.json")

    def original_document(self, profile_id: str, filename: str) -> Path:
        return self._safe_join(
            "profiles",
            self._segment(profile_id),
            "documents",
            "original",
            self._filename(filename),
        )

    def extracted_text(self, profile_id: str, doc_id: str) -> Path:
        return self._safe_join(
            "profiles",
            self._segment(profile_id),
            "documents",
            "extracted",
            f"{self._segment(doc_id)}.txt",
        )

    def document_metadata(self, profile_id: str, doc_id: str) -> Path:
        return self._safe_join(
            "profiles",
            self._segment(profile_id),
            "documents",
            "metadata",
            f"{self._segment(doc_id)}.json",
        )

    def document_audit_log(self, profile_id: str) -> Path:
        return self._safe_join(
            "profiles",
            self._segment(profile_id),
            "documents",
            "audit.jsonl",
        )

    def active_skill(self, profile_id: str, skill_id: str) -> Path:
        return self._safe_join(
            "profiles",
            self._segment(profile_id),
            "skills",
            self._segment(skill_id),
            "skill.json",
        )

    def skill_version(self, profile_id: str, skill_id: str, version: int) -> Path:
        if version < 1:
            raise ApiError("INVALID_PATH_SEGMENT", "Version must be a positive integer.")
        return self._safe_join(
            "profiles",
            self._segment(profile_id),
            "skills",
            self._segment(skill_id),
            "versions",
            f"v{version}.skill.json",
        )

    def skill_metadata(self, profile_id: str, skill_id: str) -> Path:
        return self._safe_join(
            "profiles",
            self._segment(profile_id),
            "skills",
            self._segment(skill_id),
            "metadata.json",
        )

    def audit_log(self, profile_id: str, skill_id: str) -> Path:
        return self._safe_join(
            "profiles",
            self._segment(profile_id),
            "skills",
            self._segment(skill_id),
            "audit",
            "audit.jsonl",
        )

    def outputs_dir(self, profile_id: str, skill_id: str) -> Path:
        return self._safe_join(
            "profiles",
            self._segment(profile_id),
            "skills",
            self._segment(skill_id),
            "outputs",
        )

    def _safe_join(self, *parts: str) -> Path:
        path = self.storage_root.joinpath(*parts)
        root = self.storage_root.resolve()
        resolved = path.resolve()
        if resolved != root and root not in resolved.parents:
            raise ApiError("PATH_TRAVERSAL", "Resolved path escapes the storage root.")
        return path

    @staticmethod
    def _segment(value: str) -> str:
        if not _SEGMENT_RE.fullmatch(value):
            raise ApiError(
                "INVALID_PATH_SEGMENT",
                "Path segment must be a lowercase slug with letters, numbers, underscores, or hyphens.",
            )
        return value

    @staticmethod
    def _filename(value: str) -> str:
        if "/" in value or "\\" in value or ".." in value or not _FILENAME_RE.fullmatch(value):
            raise ApiError("INVALID_FILENAME", "Filename is not safe for local storage.")
        return value
