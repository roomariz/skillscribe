import json

import pytest

from hermes_writer.api.errors import ApiError
from hermes_writer.storage.atomic_writer import (
    backup_path_for,
    recover_file_from_backup,
    recover_json_from_backup,
    write_json_atomic,
    write_text_atomic,
)
from hermes_writer.storage.file_lock import file_lock
from hermes_writer.storage.file_store import LocalFileStore
from hermes_writer.storage.path_registry import PathRegistry


def test_file_store_initializes_version_and_profiles(tmp_path):
    store = LocalFileStore(tmp_path / "data")

    store.initialize()

    assert (tmp_path / "data" / "profiles").is_dir()
    assert (tmp_path / "data" / ".version").read_text(encoding="utf-8").startswith(
        "storage_format_version=1"
    )


def test_path_registry_contracts(tmp_path):
    registry = PathRegistry(tmp_path / "data")

    assert registry.profile("muhammad") == tmp_path / "data/profiles/muhammad/profile.json"
    assert registry.original_document("muhammad", "sample-letter.pdf") == (
        tmp_path / "data/profiles/muhammad/documents/original/sample-letter.pdf"
    )
    assert registry.extracted_text("muhammad", "doc-001") == (
        tmp_path / "data/profiles/muhammad/documents/extracted/doc-001.txt"
    )
    assert registry.document_metadata("muhammad", "doc-001") == (
        tmp_path / "data/profiles/muhammad/documents/metadata/doc-001.json"
    )
    assert registry.active_skill("muhammad", "legal-drafting") == (
        tmp_path / "data/profiles/muhammad/skills/legal-drafting/skill.json"
    )
    assert registry.skill_version("muhammad", "legal-drafting", 2) == (
        tmp_path / "data/profiles/muhammad/skills/legal-drafting/versions/v2.skill.json"
    )
    assert registry.skill_metadata("muhammad", "legal-drafting") == (
        tmp_path / "data/profiles/muhammad/skills/legal-drafting/metadata.json"
    )
    assert registry.audit_log("muhammad", "legal-drafting") == (
        tmp_path / "data/profiles/muhammad/skills/legal-drafting/audit/audit.jsonl"
    )
    assert registry.outputs_dir("muhammad", "legal-drafting") == (
        tmp_path / "data/profiles/muhammad/skills/legal-drafting/outputs"
    )


@pytest.mark.parametrize("bad_value", ["../escape", "BadSlug", "name/slash", ""])
def test_path_registry_rejects_bad_segments(tmp_path, bad_value):
    registry = PathRegistry(tmp_path / "data")

    with pytest.raises(ApiError):
        registry.profile(bad_value)


@pytest.mark.parametrize("bad_filename", ["../secret.txt", "nested/file.txt", "..evil.txt"])
def test_path_registry_rejects_bad_filenames(tmp_path, bad_filename):
    registry = PathRegistry(tmp_path / "data")

    with pytest.raises(ApiError):
        registry.original_document("muhammad", bad_filename)


def test_atomic_text_write_replaces_existing_content(tmp_path):
    target = tmp_path / "profile.json"
    write_text_atomic(target, "old")

    write_text_atomic(target, "new")

    assert target.read_text(encoding="utf-8") == "new"
    assert not (tmp_path / ".profile.json.tmp").exists()


def test_atomic_json_write(tmp_path):
    target = tmp_path / "profile.json"

    write_json_atomic(target, {"profile_id": "muhammad"})

    assert json.loads(target.read_text(encoding="utf-8")) == {"profile_id": "muhammad"}


def test_backup_helper_creates_backup_before_overwrite(tmp_path):
    target = tmp_path / "profile.json"
    write_text_atomic(target, "original")

    write_text_atomic(target, "updated")

    assert backup_path_for(target).read_text(encoding="utf-8") == "original"
    assert target.read_text(encoding="utf-8") == "updated"


def test_recovery_helper_restores_missing_file_from_backup(tmp_path):
    target = tmp_path / "profile.json"
    write_text_atomic(target, "recover me")
    write_text_atomic(target, "new content")
    target.unlink()

    restored = recover_file_from_backup(target)

    assert restored is True
    assert target.read_text(encoding="utf-8") == "recover me"


def test_recovery_helper_restores_corrupt_json_from_backup(tmp_path):
    target = tmp_path / "profile.json"
    write_json_atomic(target, {"profile_id": "muhammad"})
    write_json_atomic(target, {"profile_id": "updated"})
    target.write_text("{broken", encoding="utf-8")

    restored = recover_json_from_backup(target)

    assert restored is True
    assert json.loads(target.read_text(encoding="utf-8")) == {"profile_id": "muhammad"}


def test_file_lock_context_creates_lock_file(tmp_path):
    lock_path = tmp_path / "profile.lock"

    with file_lock(lock_path):
        assert lock_path.exists()
