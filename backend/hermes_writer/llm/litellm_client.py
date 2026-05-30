from dataclasses import dataclass
import json
from typing import Any
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

    def chat_completion(
        self,
        *,
        provider: str,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1200,
    ) -> str:
        normalized = self.validate_provider(provider)
        payload = {
            "model": normalized,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        request = Request(
            f"{self.base_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8") or "{}")
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ApiError(
                "PROVIDER_UNAVAILABLE",
                "LiteLLM provider request failed.",
                status_code=503,
                details={"provider": normalized},
                recovery_hint="Verify LiteLLM is running and the provider is configured.",
            ) from exc
        return self._message_content(response_payload)

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

    @staticmethod
    def _message_content(payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ApiError("ANALYSIS_FAILED", "LiteLLM response did not include choices.", status_code=502)
        first = choices[0]
        if not isinstance(first, dict):
            raise ApiError("ANALYSIS_FAILED", "LiteLLM response choice is invalid.", status_code=502)
        message = first.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ApiError("ANALYSIS_FAILED", "LiteLLM response message is invalid.", status_code=502)
        return message["content"]
