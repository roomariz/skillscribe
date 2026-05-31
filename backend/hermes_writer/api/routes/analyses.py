from fastapi import APIRouter, Request

from hermes_writer.analysis.rule_review import RuleReviewValidator
from hermes_writer.analysis.style_analyzer import AnalysisRequest, StyleAnalyzer
from hermes_writer.api.errors import ApiError
from hermes_writer.api.schemas import AnalyzeStyleRequest, RuleReviewRequest, SuccessEnvelope
from hermes_writer.config.privacy_config import PrivacyConfigStore, PrivacyMode
from hermes_writer.llm.litellm_client import LiteLLMClient
from hermes_writer.llm.provider_detection import detect_providers

router = APIRouter(prefix="/api/profiles/{profile_id}/analyze-style")
review_router = APIRouter(prefix="/api/profiles/{profile_id}/analyses")


@router.post("", status_code=202)
async def start_analysis(
    profile_id: str,
    payload: AnalyzeStyleRequest,
    request: Request,
) -> SuccessEnvelope:
    privacy_config: PrivacyConfigStore = request.app.state.privacy_config
    privacy_mode = privacy_config.get_mode()
    statuses = {status.name: status for status in detect_providers(request.app.state.settings.ollama_base_url)}
    provider = payload.provider or _default_provider(privacy_mode, statuses)
    provider_status = statuses.get(provider)
    analyzer = StyleAnalyzer(
        document_store=request.app.state.document_store,
        litellm_client=LiteLLMClient(base_url=request.app.state.settings.litellm_base_url),
    )
    analysis = analyzer.analyze(
        AnalysisRequest(
            profile_id=profile_id,
            document_ids=payload.document_ids,
            skill_name=payload.skill_name,
            privacy_mode=privacy_mode,
            requested_provider=provider,
            provider_available=bool(provider_status and provider_status.available),
            selected_hosted_providers={
                status.name for status in statuses.values() if status.name != "ollama" and status.configured
            },
        )
    )
    request.app.state.analysis_results[analysis["analysis_id"]] = analysis
    return SuccessEnvelope(data=analysis)


@router.get("/{analysis_id}")
async def get_analysis(profile_id: str, analysis_id: str, request: Request) -> SuccessEnvelope:
    analysis = request.app.state.analysis_results.get(analysis_id)
    if not analysis or analysis.get("profile_id") not in {None, profile_id}:
        raise ApiError("ANALYSIS_NOT_FOUND", "Analysis does not exist.", status_code=404)
    return SuccessEnvelope(data=analysis)


@review_router.post("/{analysis_id}/review")
async def review_analysis_rules(
    profile_id: str,
    analysis_id: str,
    payload: RuleReviewRequest,
    request: Request,
) -> SuccessEnvelope:
    analysis = request.app.state.analysis_results.get(analysis_id)
    if not analysis or analysis.get("profile_id") not in {None, profile_id}:
        raise ApiError("ANALYSIS_NOT_FOUND", "Analysis does not exist.", status_code=404)
    review = RuleReviewValidator().validate(
        analysis=analysis,
        review=payload.model_dump(),
    )
    analysis["review"] = review
    if (
        review["summary"]["approved_count"]
        + review["summary"]["edited_count"]
        + review["summary"]["custom_count"]
        > 0
    ):
        skill = request.app.state.skill_store.create_from_review(
            profile_id=profile_id,
            analysis=analysis,
            review=review,
        )
        review["summary"]["skill_id"] = skill["metadata"]["skill_id"]
        review["summary"]["lifecycle_status"] = skill["metadata"]["lifecycle_status"]
    return SuccessEnvelope(data=review["summary"])


def _default_provider(privacy_mode: PrivacyMode, statuses: dict[str, object]) -> str:
    if privacy_mode in {PrivacyMode.LOCAL_ONLY, PrivacyMode.HYBRID}:
        return "ollama"
    for provider, status in statuses.items():
        if provider != "ollama" and getattr(status, "configured", False):
            return provider
    raise ApiError(
        "PROVIDER_UNAVAILABLE",
        "No hosted provider is configured for Cloud Allowed mode.",
        status_code=503,
        recovery_hint="Configure a hosted provider in the environment or choose another privacy mode.",
    )
