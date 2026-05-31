import json


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


def _create_pending_skill(client) -> str:
    client.post(
        "/api/profiles",
        json={"profile_id": "muhammad", "display_name": "Muhammad"},
    )
    client.app.state.analysis_results["analysis-001"] = {
        "analysis_id": "analysis-001",
        "profile_id": "muhammad",
        "skill_name": "Legal Drafting",
        "status": "completed",
        "rules": [_document_rule()],
    }
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
    return response.json()["data"]["skill_id"]


def test_skill_creation_writes_canonical_files_and_audit(client, tmp_path):
    skill_id = _create_pending_skill(client)
    root = tmp_path / f"data/profiles/muhammad/skills/{skill_id}"

    skill = json.loads((root / "skill.json").read_text(encoding="utf-8"))
    version = json.loads((root / "versions/v1.skill.json").read_text(encoding="utf-8"))
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    audit_lines = (root / "audit/audit.jsonl").read_text(encoding="utf-8").splitlines()

    assert skill["lifecycle_status"] == "PENDING"
    assert version["lifecycle_status"] == "PENDING"
    assert metadata["lifecycle_status"] == "PENDING"
    assert metadata["versions"][0]["path"] == "versions/v1.skill.json"
    assert json.loads(audit_lines[0])["event_type"] == "skill_created"


def test_skill_lifecycle_transitions_and_default(client, tmp_path):
    skill_id = _create_pending_skill(client)

    approved = client.post(f"/api/profiles/muhammad/skills/{skill_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["data"]["metadata"]["lifecycle_status"] == "APPROVED"

    activated = client.post(f"/api/profiles/muhammad/skills/{skill_id}/activate")
    assert activated.status_code == 200
    assert activated.json()["data"]["metadata"]["lifecycle_status"] == "ACTIVE"
    assert activated.json()["data"]["metadata"]["default"] is False

    defaulted = client.post(f"/api/profiles/muhammad/skills/{skill_id}/set-default")
    assert defaulted.status_code == 200
    assert defaulted.json()["data"]["metadata"]["default"] is True

    profile = client.get("/api/profiles/muhammad").json()["data"]
    assert profile["default_skill"] == skill_id

    audit_path = tmp_path / f"data/profiles/muhammad/skills/{skill_id}/audit/audit.jsonl"
    events = [json.loads(line)["event_type"] for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert events == ["skill_created", "skill_approved", "skill_activated"]


def test_skill_list_and_detail_apis(client):
    skill_id = _create_pending_skill(client)

    listed = client.get("/api/profiles/muhammad/skills")
    assert listed.status_code == 200
    assert listed.json()["data"][0]["skill_id"] == skill_id

    detail = client.get(f"/api/profiles/muhammad/skills/{skill_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["skill"]["rules"][0]["title"] == "Precise cadence"


def test_activation_requires_approval(client):
    skill_id = _create_pending_skill(client)

    response = client.post(f"/api/profiles/muhammad/skills/{skill_id}/activate")

    assert response.status_code == 409
    assert response.json()["error_code"] == "INVALID_SKILL_TRANSITION"
