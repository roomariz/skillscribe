from dataclasses import dataclass
import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from hermes_writer.api.errors import ApiError
from hermes_writer.llm.provider_router import KNOWN_PROVIDERS, validate_provider_name


@dataclass(frozen=True)
class ProviderConnection:
    provider: str
    connected: bool
    model: str | None = None


class LiteLLMClient:
    """OpenAI-compatible HTTP wrapper for LiteLLM proxy requests only."""

    def __init__(self, *, base_url: str, timeout_seconds: float = 2.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def validate_provider(self, provider: str) -> str:
        return validate_provider_name(provider)

    def provider_available(self, provider: str) -> bool:
        try:
            return self.test_connection(provider).connected
        except ApiError:
            return False

    def test_connection(self, provider: str) -> ProviderConnection:
        normalized = self.validate_provider(provider)
        if normalized not in KNOWN_PROVIDERS:
            raise ApiError("INVALID_REQUEST", "Unsupported provider.")

        request = Request(
            f"{self.base_url}/v1/models",
            headers={"Content-Type": "application/json"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8") or "{}")
        except (OSError, URLError, TimeoutError, json.JSONDecodeError):
            return ProviderConnection(provider=normalized, connected=False)

        model = self._first_provider_model(payload, normalized)
        return ProviderConnection(provider=normalized, connected=model is not None, model=model)

    @staticmethod
    def _first_provider_model(payload: dict[str, object], provider: str) -> str | None:
        models = payload.get("data")
        if not isinstance(models, list):
            return None
        for item in models:
            if not isinstance(item, dict):
                continue
            model_id = str(item.get("id", ""))
            if model_id == provider or model_id.startswith(f"{provider}/"):
                return model_id
        return None
