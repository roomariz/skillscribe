from unittest.mock import patch
import json

import pytest

from hermes_writer.analysis.style_analyzer import AnalysisRequest, StyleAnalyzer
from hermes_writer.api.errors import ApiError
from hermes_writer.llm.litellm_client import LiteLLMClient
from hermes_writer.llm.provider_detection import ProviderStatus


def _create_profile(client) -> None:
    response = client.post(
        "/api/profiles",
        json={"profile_id": "muhammad", "display_name": "Muhammad"},
    )
    assert response.status_code == 201


def _upload_text(client, text: str = "Raw private sentence. Uses precise cadence.") -> str:
    response = client.post(
        "/api/profiles/muhammad/documents/upload",
        files={"file": ("sample.txt", text.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
    return str(response.json()["data"]["doc_id"])


def _rules_json(doc_id: str) -> str:
    return json.dumps(
        {
            "rules": [
                {
                    "rule_id": "rule-001",
                    "category": "tone",
                    "title": "Precise cadence",
                    "description": "Use concise sentences with a measured cadence.",
                    "examples": {
                        "positive": "We can proceed today.",
                        "negative": "Basically, maybe we can do it.",
                    },
                    "source": "document_derived",
                    "evidence": [f"{doc_id}#s001"],
                    "confidence": 0.82,
                }
            ]
        }
    )


def _provider_statuses(*, ollama_available: bool = True, openai_available: bool = False):
    return [
        ProviderStatus(name="ollama", available=ollama_available, configured=True, model="ollama"),
        ProviderStatus(name="openai", available=openai_available, configured=openai_available),
    ]


def test_analysis_blocked_without_privacy_enforcement(client):
    _create_profile(client)
    doc_id = _upload_text(client)
    analyzer = StyleAnalyzer(
        document_store=client.app.state.document_store,
        litellm_client=LiteLLMClient(base_url="http://localhost:4000"),
    )

    with pytest.raises(ApiError) as exc_info:
        analyzer.analyze(
            AnalysisRequest(
                profile_id="muhammad",
                document_ids=[doc_id],
                skill_name="Legal",
                privacy_mode=None,  # type: ignore[arg-type]
                requested_provider="ollama",
                provider_available=True,
                selected_hosted_providers=set(),
            )
        )

    assert exc_info.value.error_code == "PRIVACY_ENFORCEMENT_REQUIRED"


def test_local_only_uses_ollama_route_only(client):
    _create_profile(client)
    doc_id = _upload_text(client)
    with (
        patch("hermes_writer.api.routes.analyses.detect_providers", return_value=_provider_statuses()),
        patch(
            "hermes_writer.analysis.style_analyzer.LiteLLMClient.chat_completion",
            return_value=_rules_json(doc_id),
        ) as completion,
    ):
        response = client.post(
            "/api/profiles/muhammad/analyze-style",
            json={"document_ids": [doc_id], "skill_name": "Legal"},
        )

    assert response.status_code == 202
    assert response.json()["data"]["provider"] == "ollama"
    assert completion.call_args.kwargs["provider"] == "ollama"


def test_hosted_prompts_exclude_raw_document_text_and_snippets(client):
    _create_profile(client)
    raw_text = "Raw private sentence. Uses precise cadence."
    doc_id = _upload_text(client, raw_text)
    client.post("/api/config/update-privacy-mode", json={"privacy_mode": "cloud_allowed"})

    def fake_completion(**kwargs):
        prompt = "\n".join(message["content"] for message in kwargs["messages"])
        assert raw_text not in prompt
        assert "Raw private sentence" not in prompt
        return _rules_json(doc_id)

    with (
        patch(
            "hermes_writer.api.routes.analyses.detect_providers",
            return_value=_provider_statuses(openai_available=True),
        ),
        patch(
            "hermes_writer.analysis.style_analyzer.LiteLLMClient.chat_completion",
            side_effect=fake_completion,
        ),
    ):
        response = client.post(
            "/api/profiles/muhammad/analyze-style",
            json={"document_ids": [doc_id], "skill_name": "Legal", "provider": "openai"},
        )

    assert response.status_code == 202
    assert response.json()["data"]["provider"] == "openai"


def test_rules_include_evidence_and_references_resolve_locally(client):
    _create_profile(client)
    doc_id = _upload_text(client)
    with (
        patch("hermes_writer.api.routes.analyses.detect_providers", return_value=_provider_statuses()),
        patch(
            "hermes_writer.analysis.style_analyzer.LiteLLMClient.chat_completion",
            return_value=_rules_json(doc_id),
        ),
    ):
        response = client.post(
            "/api/profiles/muhammad/analyze-style",
            json={"document_ids": [doc_id], "skill_name": "Legal"},
        )

    rule = response.json()["data"]["rules"][0]
    assert rule["evidence"] == [f"{doc_id}#s001"]
    assert rule["source_snippets"] == ["Raw private sentence."]
    assert rule["source"] == "document_derived"


def test_empty_document_rejected(client):
    _create_profile(client)
    doc_id = _upload_text(client)
    client.put(f"/api/profiles/muhammad/documents/{doc_id}/extracted-text", json={"extracted_text": "   "})

    with patch("hermes_writer.api.routes.analyses.detect_providers", return_value=_provider_statuses()):
        response = client.post(
            "/api/profiles/muhammad/analyze-style",
            json={"document_ids": [doc_id], "skill_name": "Legal"},
        )

    assert response.status_code == 400
    assert response.json()["error_code"] == "EMPTY_DOCUMENT"


def test_invalid_document_id_rejected(client):
    _create_profile(client)
    with patch("hermes_writer.api.routes.analyses.detect_providers", return_value=_provider_statuses()):
        response = client.post(
            "/api/profiles/muhammad/analyze-style",
            json={"document_ids": ["doc-missing"], "skill_name": "Legal"},
        )

    assert response.status_code == 404
    assert response.json()["error_code"] == "DOCUMENT_NOT_FOUND"


def test_malformed_llm_json_handled_safely(client):
    _create_profile(client)
    doc_id = _upload_text(client)
    with (
        patch("hermes_writer.api.routes.analyses.detect_providers", return_value=_provider_statuses()),
        patch(
            "hermes_writer.analysis.style_analyzer.LiteLLMClient.chat_completion",
            return_value="not-json",
        ),
    ):
        response = client.post(
            "/api/profiles/muhammad/analyze-style",
            json={"document_ids": [doc_id], "skill_name": "Legal"},
        )

    assert response.status_code == 502
    assert response.json()["error_code"] == "ANALYSIS_FAILED"


def test_document_derived_rule_without_evidence_rejected(client):
    _create_profile(client)
    doc_id = _upload_text(client)
    with (
        patch("hermes_writer.api.routes.analyses.detect_providers", return_value=_provider_statuses()),
        patch(
            "hermes_writer.analysis.style_analyzer.LiteLLMClient.chat_completion",
            return_value='{"rules":[{"rule_id":"rule-001","category":"tone","title":"Tone",'
            '"description":"Desc","examples":{"positive":"A","negative":"B"},'
            '"source":"document_derived","evidence":[],"confidence":0.7}]}',
        ),
    ):
        response = client.post(
            "/api/profiles/muhammad/analyze-style",
            json={"document_ids": [doc_id], "skill_name": "Legal"},
        )

    assert response.status_code == 422
    assert response.json()["error_code"] == "ANALYSIS_VALIDATION_FAILED"
