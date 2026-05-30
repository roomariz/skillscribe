from dataclasses import dataclass
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

from hermes_writer.llm.provider_router import HOSTED_PROVIDERS


@dataclass(frozen=True)
class ProviderStatus:
    name: str
    available: bool
    configured: bool
    model: str | None = None


PROVIDER_ENV_KEYS = {
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}


def detect_ollama(base_url: str, *, timeout_seconds: float = 0.5) -> ProviderStatus:
    request = Request(f"{base_url.rstrip('/')}/api/tags", method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            available = 200 <= response.status < 300
    except (OSError, URLError, TimeoutError):
        available = False
    return ProviderStatus(name="ollama", available=available, configured=True, model="ollama")


def detect_configured_hosted_providers() -> list[ProviderStatus]:
    statuses: list[ProviderStatus] = []
    for provider in sorted(HOSTED_PROVIDERS):
        configured = bool(os.getenv(PROVIDER_ENV_KEYS[provider]))
        statuses.append(ProviderStatus(name=provider, available=configured, configured=configured))
    return statuses


def detect_providers(ollama_base_url: str) -> list[ProviderStatus]:
    return [detect_ollama(ollama_base_url), *detect_configured_hosted_providers()]
