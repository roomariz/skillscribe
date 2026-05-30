from dataclasses import dataclass
from typing import Any

from hermes_writer.api.errors import ApiError


@dataclass(frozen=True)
class ReviewSummary:
    analysis_id: str
    approved_count: int
    rejected_count: int
    edited_count: int
    custom_count: int
    ready_for_skill_creation: bool


class RuleReviewValidator:
    def validate(self, *, analysis: dict[str, Any], review: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        evidence_refs = self._evidence_refs(analysis)
        approved = [self._validate_document_rule(rule, evidence_refs) for rule in review["approved_rules"]]
        rejected = [self._validate_document_rule(rule, evidence_refs) for rule in review["rejected_rules"]]
        edited = [self._validate_document_rule(rule, evidence_refs) for rule in review["edited_rules"]]
        custom = [self._validate_custom_rule(rule) for rule in review["custom_rules"]]

        summary = ReviewSummary(
            analysis_id=str(analysis["analysis_id"]),
            approved_count=len(approved),
            rejected_count=len(rejected),
            edited_count=len(edited),
            custom_count=len(custom),
            ready_for_skill_creation=True,
        )
        return {
            "approved_rules": approved,
            "rejected_rules": rejected,
            "edited_rules": edited,
            "custom_rules": custom,
            "summary": summary.__dict__,
        }

    def _evidence_refs(self, analysis: dict[str, Any]) -> set[str]:
        refs: set[str] = set()
        for rule in analysis.get("rules", []):
            if isinstance(rule, dict):
                refs.update(str(reference) for reference in rule.get("evidence", []))
        return refs

    def _validate_document_rule(
        self,
        rule: dict[str, Any],
        evidence_refs: set[str],
    ) -> dict[str, Any]:
        if rule.get("source") != "document_derived":
            raise ApiError(
                "REVIEW_VALIDATION_FAILED",
                "Reviewed analysis rules must keep source=document_derived.",
                status_code=422,
            )
        evidence = rule.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ApiError(
                "REVIEW_VALIDATION_FAILED",
                "Document-derived review rules must retain evidence.",
                status_code=422,
            )
        missing = [str(reference) for reference in evidence if str(reference) not in evidence_refs]
        if missing:
            raise ApiError(
                "REVIEW_VALIDATION_FAILED",
                "Review rule evidence reference does not resolve locally.",
                status_code=422,
                details={"evidence": missing},
            )
        return self._base_rule(rule, source="document_derived", evidence=[str(ref) for ref in evidence])

    def _validate_custom_rule(self, rule: dict[str, Any]) -> dict[str, Any]:
        if rule.get("source") != "user_authored":
            raise ApiError(
                "REVIEW_VALIDATION_FAILED",
                "Custom rules must use source=user_authored.",
                status_code=422,
            )
        if rule.get("evidence") is not None:
            raise ApiError(
                "REVIEW_VALIDATION_FAILED",
                "Custom rules must use evidence=null.",
                status_code=422,
            )
        return self._base_rule(rule, source="user_authored", evidence=None)

    def _base_rule(
        self,
        rule: dict[str, Any],
        *,
        source: str,
        evidence: list[str] | None,
    ) -> dict[str, Any]:
        confidence = rule.get("confidence", 1.0 if source == "user_authored" else None)
        if not isinstance(confidence, int | float) or confidence < 0 or confidence > 1:
            raise ApiError(
                "REVIEW_VALIDATION_FAILED",
                "Rule confidence must be between 0 and 1.",
                status_code=422,
            )
        examples = rule.get("examples")
        if not isinstance(examples, dict):
            raise ApiError("REVIEW_VALIDATION_FAILED", "Rule examples are invalid.", status_code=422)
        source_snippets = rule.get("source_snippets", [])
        if source == "document_derived" and (
            not isinstance(source_snippets, list) or not source_snippets
        ):
            raise ApiError(
                "REVIEW_VALIDATION_FAILED",
                "Document-derived review rules must retain source snippets.",
                status_code=422,
            )
        return {
            "rule_id": self._required_str(rule, "rule_id"),
            "category": self._required_str(rule, "category"),
            "title": self._required_str(rule, "title"),
            "description": self._required_str(rule, "description"),
            "examples": {
                "positive": self._required_str(examples, "positive"),
                "negative": self._required_str(examples, "negative"),
            },
            "confidence": float(confidence),
            "source": source,
            "evidence": evidence,
            "source_snippets": source_snippets if source == "document_derived" else [],
        }

    @staticmethod
    def _required_str(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ApiError(
                "REVIEW_VALIDATION_FAILED",
                "Rule is missing a required string field.",
                status_code=422,
                details={"field": key},
            )
        return value
