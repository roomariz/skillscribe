from dataclasses import dataclass
from datetime import datetime, timezone
import json
import uuid
from typing import Any

from hermes_writer.api.errors import ApiError
from hermes_writer.analysis.evidence_indexer import EvidenceIndex, EvidenceIndexer
from hermes_writer.config.privacy_config import PrivacyMode
from hermes_writer.llm.litellm_client import LiteLLMClient
from hermes_writer.llm.privacy_guard import OLLAMA_PROVIDER
from hermes_writer.llm.provider_router import HOSTED_PROVIDERS, resolve_route
from hermes_writer.storage.document_store import DocumentStore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class AnalysisRequest:
    profile_id: str
    document_ids: list[str]
    skill_name: str
    privacy_mode: PrivacyMode
    requested_provider: str
    provider_available: bool
    selected_hosted_providers: set[str]


class StyleAnalyzer:
    def __init__(self, *, document_store: DocumentStore, litellm_client: LiteLLMClient) -> None:
        self.document_store = document_store
        self.litellm_client = litellm_client
        self.evidence_indexer = EvidenceIndexer()

    def analyze(self, request: AnalysisRequest) -> dict[str, Any]:
        if request.privacy_mode is None:
            raise ApiError(
                "PRIVACY_ENFORCEMENT_REQUIRED",
                "Privacy mode must be selected before style analysis can run.",
                status_code=400,
                recovery_hint="Select a privacy mode in Settings before analyzing documents.",
            )
        if not request.document_ids:
            raise ApiError("INVALID_REQUEST", "At least one document is required.")

        route = resolve_route(
            privacy_mode=request.privacy_mode,
            requested_provider=request.requested_provider,
            operation_type="analysis",
            provider_available=request.provider_available,
            selected_hosted_providers=request.selected_hosted_providers,
        )
        documents = self._load_documents(request.profile_id, request.document_ids)
        evidence_index = self.evidence_indexer.build(documents)
        messages = self._build_messages(
            skill_name=request.skill_name,
            documents=documents,
            evidence_index=evidence_index,
            privacy_mode=route.privacy_mode,
            provider=route.provider,
        )
        self._validate_hosted_prompt(route.provider, messages, documents, evidence_index)
        llm_content = self.litellm_client.chat_completion(
            provider=route.provider,
            messages=messages,
        )
        rules = self._parse_rules(llm_content, evidence_index)
        analysis_id = f"analysis-{uuid.uuid4().hex[:12]}"
        return {
            "analysis_id": analysis_id,
            "profile_id": request.profile_id,
            "status": "completed",
            "progress": 1.0,
            "skill_name": request.skill_name,
            "provider": route.provider,
            "privacy_mode": route.privacy_mode.value,
            "document_ids": request.document_ids,
            "rules": rules,
            "created_at": _now_iso(),
        }

    def _load_documents(self, profile_id: str, document_ids: list[str]) -> dict[str, str]:
        documents: dict[str, str] = {}
        for doc_id in document_ids:
            metadata = self.document_store.get_document(profile_id, doc_id)
            text = str(metadata.get("extracted_text", ""))
            if not text.strip():
                raise ApiError(
                    "EMPTY_DOCUMENT",
                    "Extracted text is empty and cannot be analyzed.",
                    status_code=400,
                    details={"doc_id": doc_id},
                )
            documents[doc_id] = text
        return documents

    def _build_messages(
        self,
        *,
        skill_name: str,
        documents: dict[str, str],
        evidence_index: EvidenceIndex,
        privacy_mode: PrivacyMode,
        provider: str,
    ) -> list[dict[str, str]]:
        schema = (
            "Return JSON only with a rules array. Each rule must include rule_id, category, "
            "title, description, examples.positive, examples.negative, source=document_derived, "
            "evidence, and confidence."
        )
        if privacy_mode == PrivacyMode.LOCAL_ONLY and provider == OLLAMA_PROVIDER:
            body = "\n\n".join(f"Document {doc_id}:\n{text}" for doc_id, text in documents.items())
            evidence = "\n".join(
                f"{snippet.reference}: {snippet.text}" for snippet in evidence_index.snippets
            )
            user_content = f"Skill name: {skill_name}\n\nEvidence:\n{evidence}\n\nDocuments:\n{body}"
        else:
            refs = ", ".join(evidence_index.references())
            doc_ids = ", ".join(documents)
            user_content = (
                f"Skill name: {skill_name}\nDocument IDs: {doc_ids}\n"
                f"Allowed local evidence references: {refs}\n"
                "Do not infer from raw source text; use only abstract style observations."
            )
        return [
            {"role": "system", "content": "Extract evidence-linked writing style rules."},
            {"role": "user", "content": f"{schema}\n\n{user_content}"},
        ]

    def _validate_hosted_prompt(
        self,
        provider: str,
        messages: list[dict[str, str]],
        documents: dict[str, str],
        evidence_index: EvidenceIndex,
    ) -> None:
        if provider not in HOSTED_PROVIDERS:
            return
        prompt = "\n".join(message["content"] for message in messages)
        forbidden = [text for text in documents.values() if text.strip()]
        forbidden.extend(snippet.text for snippet in evidence_index.snippets if snippet.text.strip())
        if any(text in prompt for text in forbidden):
            raise ApiError(
                "PRIVACY_ENFORCEMENT_REQUIRED",
                "Hosted-provider prompt contains raw source text or evidence snippets.",
                status_code=400,
                recovery_hint="Use Local Only for raw extracted text analysis.",
            )

    def _parse_rules(self, content: str, evidence_index: EvidenceIndex) -> list[dict[str, Any]]:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ApiError(
                "ANALYSIS_FAILED",
                "Style analysis returned malformed JSON.",
                status_code=502,
                recovery_hint="Retry analysis or choose another provider.",
            ) from exc
        rules = payload.get("rules") if isinstance(payload, dict) else None
        if not isinstance(rules, list):
            raise ApiError("ANALYSIS_FAILED", "Style analysis did not return a rules array.", status_code=502)

        validated: list[dict[str, Any]] = []
        for raw_rule in rules:
            if not isinstance(raw_rule, dict):
                raise ApiError("ANALYSIS_VALIDATION_FAILED", "Rule payload is invalid.", status_code=422)
            evidence = raw_rule.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                raise ApiError(
                    "ANALYSIS_VALIDATION_FAILED",
                    "Document-derived rules must include evidence references.",
                    status_code=422,
                )
            source_snippets = [evidence_index.resolve(str(reference)).text for reference in evidence]
            confidence = raw_rule.get("confidence")
            if not isinstance(confidence, int | float) or confidence < 0 or confidence > 1:
                raise ApiError(
                    "ANALYSIS_VALIDATION_FAILED",
                    "Rule confidence must be between 0 and 1.",
                    status_code=422,
                )
            examples = raw_rule.get("examples")
            if not isinstance(examples, dict):
                raise ApiError("ANALYSIS_VALIDATION_FAILED", "Rule examples are invalid.", status_code=422)
            validated.append(
                {
                    "rule_id": self._required_str(raw_rule, "rule_id"),
                    "category": self._required_str(raw_rule, "category"),
                    "title": self._required_str(raw_rule, "title"),
                    "description": self._required_str(raw_rule, "description"),
                    "examples": {
                        "positive": self._required_str(examples, "positive"),
                        "negative": self._required_str(examples, "negative"),
                    },
                    "source": "document_derived",
                    "evidence": [str(reference) for reference in evidence],
                    "source_snippets": source_snippets,
                    "confidence": float(confidence),
                }
            )
        return validated

    @staticmethod
    def _required_str(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ApiError(
                "ANALYSIS_VALIDATION_FAILED",
                "Rule payload is missing a required string field.",
                status_code=422,
                details={"field": key},
            )
        return value
