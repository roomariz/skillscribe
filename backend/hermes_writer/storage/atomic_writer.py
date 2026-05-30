import json
import os
from pathlib import Path
import shutil
from typing import Any

from hermes_writer.storage.file_lock import file_lock


def backup_path_for(path: Path) -> Path:
    return path.with_name(f"{path.name}.bak")


def backup_existing_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup_path = backup_path_for(path)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)
    return backup_path


def recover_file_from_backup(path: Path, *, corrupt: bool = False) -> bool:
    backup_path = backup_path_for(path)
    if path.exists() and not corrupt:
        return False
    if not backup_path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, path)
    return True


def recover_json_from_backup(path: Path) -> bool:
    if not path.exists():
        return recover_file_from_backup(path)
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return recover_file_from_backup(path, corrupt=True)
    return False


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
    backup_existing_file(path)
    os.replace(temp_path, path)


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    write_text_atomic(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def append_jsonl_atomic(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
    lock_path = path.with_name(f".{path.name}.lock")
    with file_lock(lock_path):
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
