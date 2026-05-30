from datetime import datetime, timezone
import json
from pathlib import Path
import uuid
from typing import Any

from hermes_writer.api.errors import ApiError
from hermes_writer.extraction.document_extractor import extract_text
from hermes_writer.storage.atomic_writer import append_jsonl_atomic, write_json_atomic, write_text_atomic
from hermes_writer.storage.path_registry import PathRegistry
from hermes_writer.storage.profile_store import ProfileStore

MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024
ALLOWED_FILE_TYPES = {"pdf", "docx", "txt"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _counts(text: str) -> tuple[int, int]:
    return len(text.split()), len(text)


class DocumentStore:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root
        self.registry = PathRegistry(storage_root)
        self.profile_store = ProfileStore(storage_root)

    def upload_document(self, profile_id: str, filename: str, content: bytes) -> dict[str, Any]:
        self.profile_store.get_profile(profile_id)
        safe_filename = self.registry.original_document(profile_id, filename).name
        file_type = self._file_type(safe_filename)
        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            raise ApiError(
                "FILE_TOO_LARGE",
                "Uploaded documents must be 50 MB or smaller.",
                status_code=413,
            )
        if not content:
            raise ApiError("INVALID_REQUEST", "Uploaded document is empty.")

        original_path = self.registry.original_document(profile_id, safe_filename)
        if original_path.exists():
            raise ApiError(
                "FILE_UPLOAD_FAILED",
                "A document with this filename already exists for the profile.",
                status_code=409,
            )

        doc_id = f"doc-{uuid.uuid4().hex[:12]}"
        original_path.parent.mkdir(parents=True, exist_ok=True)
        original_path.write_bytes(content)
        uploaded_at = _now_iso()
        self._append_audit_event(
            profile_id,
            {
                "timestamp": uploaded_at,
                "event_type": "document_uploaded",
                "actor": "user",
                "doc_id": doc_id,
                "filename": safe_filename,
            },
        )

        extraction_started_at = uploaded_at
        text, method = extract_text(original_path, file_type)
        extraction_completed_at = _now_iso()
        word_count, character_count = _counts(text)

        write_text_atomic(self.registry.extracted_text(profile_id, doc_id), text)
        metadata = {
            "doc_id": doc_id,
            "profile_id": profile_id,
            "original_filename": safe_filename,
            "file_type": file_type,
            "file_size_bytes": len(content),
            "uploaded_at": extraction_started_at,
            "extraction_started_at": extraction_started_at,
            "extraction_completed_at": extraction_completed_at,
            "extraction_method": method,
            "extracted_text_location": f"extracted/{doc_id}.txt",
            "word_count": word_count,
            "character_count": character_count,
            "status": "extracted",
            "error_message": None,
        }
        write_json_atomic(self.registry.document_metadata(profile_id, doc_id), metadata)
        self._append_audit_event(
            profile_id,
            {
                "timestamp": extraction_completed_at,
                "event_type": "document_extracted",
                "actor": "system",
                "doc_id": doc_id,
                "extraction_method": method,
            },
        )
        return metadata

    def list_documents(self, profile_id: str, *, status: str | None = None) -> list[dict[str, Any]]:
        self.profile_store.get_profile(profile_id)
        metadata_dir = self.registry.profile(profile_id).parent / "documents" / "metadata"
        if not metadata_dir.exists():
            return []
        documents = [self._read_metadata_path(path) for path in sorted(metadata_dir.glob("*.json"))]
        if status:
            documents = [document for document in documents if document.get("status") == status]
        return documents

    def get_document(self, profile_id: str, doc_id: str) -> dict[str, Any]:
        metadata = self._read_metadata(profile_id, doc_id)
        metadata["extracted_text"] = self.read_extracted_text(profile_id, doc_id)
        return metadata

    def preview_extracted_text(
        self,
        profile_id: str,
        doc_id: str,
        *,
        limit: int = 4000,
    ) -> dict[str, Any]:
        metadata = self._read_metadata(profile_id, doc_id)
        text = self.read_extracted_text(profile_id, doc_id)
        return {
            "doc_id": doc_id,
            "filename": metadata["original_filename"],
            "preview": text[:limit],
            "character_count": len(text),
            "truncated": len(text) > limit,
        }

    def update_extracted_text(
        self,
        profile_id: str,
        doc_id: str,
        extracted_text: str,
    ) -> dict[str, Any]:
        metadata = self._read_metadata(profile_id, doc_id)
        word_count, character_count = _counts(extracted_text)
        write_text_atomic(self.registry.extracted_text(profile_id, doc_id), extracted_text)
        metadata.update(
            {
                "extraction_completed_at": _now_iso(),
                "extraction_method": "manual",
                "word_count": word_count,
                "character_count": character_count,
                "status": "extracted",
                "error_message": None,
            }
        )
        write_json_atomic(self.registry.document_metadata(profile_id, doc_id), metadata)
        metadata["extracted_text"] = extracted_text
        return metadata

    def count_documents(self) -> int:
        metadata_root = self.storage_root / "profiles"
        if not metadata_root.exists():
            return 0
        return sum(1 for path in metadata_root.glob("*/documents/metadata/*.json") if path.is_file())

    def read_extracted_text(self, profile_id: str, doc_id: str) -> str:
        path = self.registry.extracted_text(profile_id, doc_id)
        if not path.exists():
            raise ApiError("DOCUMENT_NOT_FOUND", "Document does not exist.", status_code=404)
        return path.read_text(encoding="utf-8")

    def _append_audit_event(self, profile_id: str, event: dict[str, Any]) -> None:
        append_jsonl_atomic(self.registry.document_audit_log(profile_id), event)

    def _read_metadata(self, profile_id: str, doc_id: str) -> dict[str, Any]:
        self.profile_store.get_profile(profile_id)
        path = self.registry.document_metadata(profile_id, doc_id)
        if not path.exists():
            raise ApiError("DOCUMENT_NOT_FOUND", "Document does not exist.", status_code=404)
        return self._read_metadata_path(path)

    @staticmethod
    def _read_metadata_path(path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ApiError(
                "STORAGE_ERROR",
                "Document metadata is not valid JSON.",
                status_code=500,
            ) from exc
        if not isinstance(data, dict) or "doc_id" not in data:
            raise ApiError("STORAGE_ERROR", "Document metadata is invalid.", status_code=500)
        return data

    @staticmethod
    def _file_type(filename: str) -> str:
        file_type = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if file_type not in ALLOWED_FILE_TYPES:
            raise ApiError(
                "INVALID_FILE_TYPE",
                "Only PDF, DOCX, and TXT files are supported.",
                details={"allowed": sorted(ALLOWED_FILE_TYPES)},
            )
        return file_type
