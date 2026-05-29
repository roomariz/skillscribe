from collections.abc import Iterator

from fastapi.testclient import TestClient
import pytest

from hermes_writer.api.app import create_app
from hermes_writer.config.settings import Settings


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    app = create_app(
        Settings(
            storage_root=tmp_path / "data",
            cors_origin="http://localhost:5173",
            log_level="INFO",
            privacy_mode="local_only",
            litellm_base_url="http://localhost:4000",
            ollama_base_url="http://localhost:11434",
        )
    )
    with TestClient(app) as test_client:
        yield test_client

