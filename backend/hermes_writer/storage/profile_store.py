from pathlib import Path

from hermes_writer.storage.file_store import LocalFileStore


class ProfileStore:
    def __init__(self, storage_root: Path) -> None:
        self.file_store = LocalFileStore(storage_root)

    def initialize(self) -> None:
        self.file_store.initialize()

    def count_profiles(self) -> int:
        return self.file_store.count_profiles()

