from pathlib import Path

from hermes_writer.storage.atomic_writer import write_text_atomic


class LocalFileStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.profiles_root = root / "profiles"
        self.version_file = root / ".version"

    def initialize(self) -> None:
        self.profiles_root.mkdir(parents=True, exist_ok=True)
        if not self.version_file.exists():
            write_text_atomic(
                self.version_file,
                "storage_format_version=1\nhermes_writer_version=1.0.0\n",
            )

    def is_available(self) -> bool:
        return self.root.exists() and self.profiles_root.exists()

    def count_profiles(self) -> int:
        if not self.profiles_root.exists():
            return 0
        return sum(1 for path in self.profiles_root.iterdir() if path.is_dir())

