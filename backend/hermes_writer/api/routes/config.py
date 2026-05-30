from dataclasses import asdict

from fastapi import APIRouter, Request

from hermes_writer.api.schemas import (
    PrivacyModeUpdateRequest,
    ProviderTestRequest,
    SuccessEnvelope,
)
from hermes_writer.config.privacy_config import PrivacyConfigStore
from hermes_writer.llm.litellm_client import LiteLLMClient
from hermes_writer.llm.privacy_guard import OperationType
from hermes_writer.llm.provider_detection import detect_providers
from hermes_writer.llm.provider_router import resolve_route

router = APIRouter(prefix="/api/config")


def _config_payload(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    privacy_config: PrivacyConfigStore = request.app.state.privacy_config
    providers = [asdict(status) for status in detect_providers(settings.ollama_base_url)]
    return {
        "providers": providers,
        "privacy_mode": privacy_config.get_mode().value,
        "max_upload_size_mb": 50,
        "storage_path": settings.storage_root.as_posix(),
    }


@router.get("")
async def get_config(request: Request) -> SuccessEnvelope:
    return SuccessEnvelope(data=_config_payload(request))


@router.post("/update-privacy-mode")
async def update_privacy_mode(
    payload: PrivacyModeUpdateRequest,
    request: Request,
) -> SuccessEnvelope:
    privacy_config: PrivacyConfigStore = request.app.state.privacy_config
    privacy_config.set_mode(payload.privacy_mode)
    return SuccessEnvelope(data=_config_payload(request))


@router.post("/test-provider")
async def test_provider(payload: ProviderTestRequest, request: Request) -> SuccessEnvelope:
    settings = request.app.state.settings
    privacy_config: PrivacyConfigStore = request.app.state.privacy_config
    statuses = {status.name: status for status in detect_providers(settings.ollama_base_url)}
    provider = payload.provider.strip().lower()
    status = statuses.get(provider)
    route = resolve_route(
        privacy_mode=privacy_config.get_mode(),
        requested_provider=provider,
        operation_type=OperationType.PROVIDER_TEST,
        provider_available=bool(status and status.available),
        selected_hosted_providers={
            item.name for item in statuses.values() if item.configured and item.name != "ollama"
        },
    )
    client = LiteLLMClient(base_url=settings.litellm_base_url)
    connection = client.test_connection(route.provider)
    return SuccessEnvelope(
        data={
            "provider": connection.provider,
            "connected": connection.connected,
            "model": connection.model,
        }
    )
