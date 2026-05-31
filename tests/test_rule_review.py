from copy import deepcopy


def _analysis(rule: dict | None = None) -> dict:
    base_rule = rule or _document_rule()
    return {
        "analysis_id": "analysis-001",
        "profile_id": "muhammad",
        "skill_name": "Legal Drafting",
        "status": "completed",
        "rules": [base_rule],
    }


def _document_rule(**overrides) -> dict:
    rule = {
        "rule_id": "rule-001",
        "category": "tone",
        "title": "Precise cadence",
        "description": "Use concise sentences.",
        "examples": {"positive": "Proceed today.", "negative": "Maybe later perhaps."},
        "confidence": 0.82,
        "source": "document_derived",
        "evidence": ["doc-001#s001"],
        "source_snippets": ["Raw private sentence."],
    }
    rule.update(overrides)
    return rule


def _custom_rule(**overrides) -> dict:
    rule = {
        "rule_id": "custom-001",
        "category": "structure",
        "title": "Use headings",
        "description": "Add a heading before major sections.",
        "examples": {"positive": "Summary\nDetails", "negative": "Summary details"},
        "confidence": 1.0,
        "source": "user_authored",
        "evidence": None,
        "source_snippets": [],
    }
    rule.update(overrides)
    return rule


def _install_analysis(client, analysis: dict | None = None) -> None:
    client.post(
        "/api/profiles",
        json={"profile_id": "muhammad", "display_name": "Muhammad"},
    )
    client.app.state.analysis_results["analysis-001"] = analysis or _analysis()


def test_approve_rules_succeeds(client, tmp_path):
    _install_analysis(client)

    response = client.post(
        "/api/profiles/muhammad/analyses/analysis-001/review",
        json={
            "approved_rules": [_document_rule()],
            "rejected_rules": [],
            "edited_rules": [],
            "custom_rules": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["approved_count"] == 1
    assert (tmp_path / "data/profiles/muhammad/skills/legal-drafting/skill.json").exists()
    assert (tmp_path / "data/profiles/muhammad/skills/legal-drafting/metadata.json").exists()
    assert (
        tmp_path / "data/profiles/muhammad/skills/legal-drafting/versions/v1.skill.json"
    ).exists()


def test_reject_rules_succeeds(client):
    _install_analysis(client)

    response = client.post(
        "/api/profiles/muhammad/analyses/analysis-001/review",
        json={
            "approved_rules": [],
            "rejected_rules": [_document_rule()],
            "edited_rules": [],
            "custom_rules": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["rejected_count"] == 1


def test_edited_rules_preserved(client):
    _install_analysis(client)
    edited = _document_rule(title="Edited title", description="Edited description.")

    response = client.post(
        "/api/profiles/muhammad/analyses/analysis-001/review",
        json={
            "approved_rules": [],
            "rejected_rules": [],
            "edited_rules": [edited],
            "custom_rules": [],
        },
    )

    assert response.status_code == 200
    review = client.app.state.analysis_results["analysis-001"]["review"]
    assert review["edited_rules"][0]["title"] == "Edited title"
    assert review["edited_rules"][0]["evidence"] == ["doc-001#s001"]


def test_custom_rule_validation(client):
    _install_analysis(client)

    response = client.post(
        "/api/profiles/muhammad/analyses/analysis-001/review",
        json={
            "approved_rules": [],
            "rejected_rules": [],
            "edited_rules": [],
            "custom_rules": [_custom_rule()],
        },
    )

    assert response.status_code == 200
    review = client.app.state.analysis_results["analysis-001"]["review"]
    assert review["custom_rules"][0]["source"] == "user_authored"
    assert review["custom_rules"][0]["evidence"] is None


def test_document_derived_evidence_required(client):
    _install_analysis(client)
    rule = _document_rule(evidence=[])

    response = client.post(
        "/api/profiles/muhammad/analyses/analysis-001/review",
        json={
            "approved_rules": [rule],
            "rejected_rules": [],
            "edited_rules": [],
            "custom_rules": [],
        },
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "REVIEW_VALIDATION_FAILED"


def test_invalid_evidence_rejected(client):
    _install_analysis(client)
    rule = _document_rule(evidence=["doc-001#missing"])

    response = client.post(
        "/api/profiles/muhammad/analyses/analysis-001/review",
        json={
            "approved_rules": [rule],
            "rejected_rules": [],
            "edited_rules": [],
            "custom_rules": [],
        },
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "REVIEW_VALIDATION_FAILED"


def test_confidence_validation(client):
    _install_analysis(client)
    rule = _document_rule(confidence=1.2)

    response = client.post(
        "/api/profiles/muhammad/analyses/analysis-001/review",
        json={
            "approved_rules": [rule],
            "rejected_rules": [],
            "edited_rules": [],
            "custom_rules": [],
        },
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "REVIEW_VALIDATION_FAILED"


def test_review_summary_counts_correct(client):
    _install_analysis(client)
    edited = deepcopy(_document_rule())
    edited["title"] = "Edited"

    response = client.post(
        "/api/profiles/muhammad/analyses/analysis-001/review",
        json={
            "approved_rules": [_document_rule()],
            "rejected_rules": [_document_rule(rule_id="rule-002")],
            "edited_rules": [edited],
            "custom_rules": [_custom_rule()],
        },
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "analysis_id": "analysis-001",
        "approved_count": 1,
        "rejected_count": 1,
        "edited_count": 1,
        "custom_count": 1,
        "ready_for_skill_creation": True,
        "skill_id": "legal-drafting",
        "lifecycle_status": "PENDING",
    }
