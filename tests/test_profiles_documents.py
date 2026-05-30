from io import BytesIO
import json

import fitz
from docx import Document

from hermes_writer.storage.document_store import MAX_UPLOAD_SIZE_BYTES
from hermes_writer.storage.profile_store import ProfileStore


def _create_profile(client, profile_id: str = "muhammad") -> dict[str, object]:
    response = client.post(
        "/api/profiles",
        json={
            "profile_id": profile_id,
            "display_name": "Muhammad",
            "description": "Legal drafting",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def _docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def test_profile_store_create_list_update_and_soft_delete(tmp_path):
    store = ProfileStore(tmp_path / "data")
    store.initialize()

    profile = store.create_profile(
        profile_id="muhammad",
        display_name="Muhammad",
        description="Original",
    )

    assert profile["profile_id"] == "muhammad"
    assert (tmp_path / "data/profiles/muhammad/profile.json").exists()
    assert (tmp_path / "data/profiles/muhammad/documents/original").is_dir()
    assert store.list_profiles()[0]["display_name"] == "Muhammad"

    updated = store.update_profile("muhammad", display_name="Muhammad Ali")
    assert updated["display_name"] == "Muhammad Ali"

    store.soft_delete_profile("muhammad")

    assert store.list_profiles() == []
    deleted = json.loads((tmp_path / "data/profiles/muhammad/profile.json").read_text())
    assert deleted["deleted_at"] is not None


def test_profile_api_lifecycle(client):
    _create_profile(client)

    list_response = client.get("/api/profiles")
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["profile_id"] == "muhammad"

    update_response = client.put(
        "/api/profiles/muhammad",
        json={"display_name": "Muhammad Ali", "description": "Updated"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["display_name"] == "Muhammad Ali"

    delete_response = client.delete("/api/profiles/muhammad")
    assert delete_response.status_code == 204
    assert client.get("/api/profiles/muhammad").status_code == 404


def test_txt_upload_stores_original_metadata_and_extracted_text(client, tmp_path):
    _create_profile(client)

    response = client.post(
        "/api/profiles/muhammad/documents/upload",
        files={"file": ("sample.txt", b"Hello local writer\nThis is extracted.", "text/plain")},
    )

    assert response.status_code == 201
    metadata = response.json()["data"]
    doc_id = metadata["doc_id"]
    assert metadata["file_type"] == "txt"
    assert metadata["extraction_method"] == "plain-text"
    assert metadata["word_count"] == 6
    assert (tmp_path / "data/profiles/muhammad/documents/original/sample.txt").exists()
    assert (tmp_path / f"data/profiles/muhammad/documents/extracted/{doc_id}.txt").read_text(
        encoding="utf-8"
    ) == "Hello local writer\nThis is extracted."
    assert (tmp_path / f"data/profiles/muhammad/documents/metadata/{doc_id}.json").exists()

    preview = client.get(f"/api/profiles/muhammad/documents/{doc_id}/preview")
    assert preview.status_code == 200
    assert preview.json()["data"]["preview"].startswith("Hello local writer")


def test_txt_upload_preserves_text_exactly(client, tmp_path):
    _create_profile(client)
    text = "  leading spaces\n\nmiddle line\ntrailing spaces   \n"

    response = client.post(
        "/api/profiles/muhammad/documents/upload",
        files={"file": ("exact.txt", text.encode("utf-8"), "text/plain")},
    )

    assert response.status_code == 201
    doc_id = response.json()["data"]["doc_id"]
    extracted_path = tmp_path / f"data/profiles/muhammad/documents/extracted/{doc_id}.txt"
    extracted = extracted_path.read_text(encoding="utf-8")
    assert extracted == text
    assert extracted.startswith("  leading")
    assert "trailing spaces   \n" in extracted
    assert extracted.endswith("\n")
    assert "\n\nmiddle line" in extracted


def test_manual_extracted_text_update(client):
    _create_profile(client)
    upload = client.post(
        "/api/profiles/muhammad/documents/upload",
        files={"file": ("sample.txt", b"Original text", "text/plain")},
    )
    doc_id = upload.json()["data"]["doc_id"]

    response = client.put(
        f"/api/profiles/muhammad/documents/{doc_id}/extracted-text",
        json={"extracted_text": "Manual replacement text"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["extraction_method"] == "manual"
    assert response.json()["data"]["word_count"] == 3
    preview = client.get(f"/api/profiles/muhammad/documents/{doc_id}/preview")
    assert preview.json()["data"]["preview"] == "Manual replacement text"


def test_upload_rejects_invalid_type_and_size(client):
    _create_profile(client)

    invalid_type = client.post(
        "/api/profiles/muhammad/documents/upload",
        files={"file": ("bad.md", b"# nope", "text/markdown")},
    )
    assert invalid_type.status_code == 400
    assert invalid_type.json()["error_code"] == "INVALID_FILE_TYPE"

    too_large = client.post(
        "/api/profiles/muhammad/documents/upload",
        files={"file": ("large.txt", b"x" * (MAX_UPLOAD_SIZE_BYTES + 1), "text/plain")},
    )
    assert too_large.status_code == 413
    assert too_large.json()["error_code"] == "FILE_TOO_LARGE"


def test_docx_and_pdf_extractors(client):
    _create_profile(client)

    docx_response = client.post(
        "/api/profiles/muhammad/documents/upload",
        files={
            "file": (
                "letter.docx",
                _docx_bytes("DOCX extraction works"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert docx_response.status_code == 201
    assert docx_response.json()["data"]["extraction_method"] == "python-docx"

    pdf_response = client.post(
        "/api/profiles/muhammad/documents/upload",
        files={"file": ("letter.pdf", _pdf_bytes("PDF extraction works"), "application/pdf")},
    )
    assert pdf_response.status_code == 201
    assert pdf_response.json()["data"]["extraction_method"] == "pymupdf"

    documents = client.get("/api/profiles/muhammad/documents")
    assert len(documents.json()["data"]) == 2


def test_extraction_failures_include_recovery_hints(client):
    _create_profile(client)

    pdf_response = client.post(
        "/api/profiles/muhammad/documents/upload",
        files={"file": ("broken.pdf", b"not a pdf", "application/pdf")},
    )
    assert pdf_response.status_code == 500
    assert pdf_response.json()["error_code"] == "EXTRACTION_FAILED"
    assert (
        pdf_response.json()["recovery_hint"]
        == "Verify the PDF is not encrypted or corrupted. You may also paste the extracted text manually."
    )

    docx_response = client.post(
        "/api/profiles/muhammad/documents/upload",
        files={
            "file": (
                "broken.docx",
                b"not a docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert docx_response.status_code == 500
    assert docx_response.json()["error_code"] == "EXTRACTION_FAILED"
    assert (
        docx_response.json()["recovery_hint"]
        == "Verify the DOCX file is valid and not corrupted. You may also paste the extracted text manually."
    )

    txt_response = client.post(
        "/api/profiles/muhammad/documents/upload",
        files={"file": ("broken.txt", b"\xff\xfe\xfa", "text/plain")},
    )
    assert txt_response.status_code == 400
    assert txt_response.json()["error_code"] == "EXTRACTION_FAILED"
    assert (
        txt_response.json()["recovery_hint"]
        == "Verify the file is UTF-8 encoded. You may also paste the extracted text manually."
    )


def test_document_upload_writes_metadata_and_audit_events(client, tmp_path):
    _create_profile(client)

    response = client.post(
        "/api/profiles/muhammad/documents/upload",
        files={"file": ("audit.txt", b"Audit text", "text/plain")},
    )

    assert response.status_code == 201
    metadata = response.json()["data"]
    doc_id = metadata["doc_id"]
    metadata_path = tmp_path / f"data/profiles/muhammad/documents/metadata/{doc_id}.json"
    audit_path = tmp_path / "data/profiles/muhammad/documents/audit.jsonl"
    assert metadata_path.exists()
    assert metadata_path.read_text(encoding="utf-8")

    events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert events == [
        {
            "timestamp": metadata["uploaded_at"],
            "event_type": "document_uploaded",
            "actor": "user",
            "doc_id": doc_id,
            "filename": "audit.txt",
        },
        {
            "timestamp": metadata["extraction_completed_at"],
            "event_type": "document_extracted",
            "actor": "system",
            "doc_id": doc_id,
            "extraction_method": "plain-text",
        },
    ]
