from dataclasses import dataclass
import re

from hermes_writer.api.errors import ApiError


@dataclass(frozen=True)
class EvidenceSnippet:
    doc_id: str
    snippet_id: str
    reference: str
    text: str


class EvidenceIndex:
    def __init__(self, snippets: list[EvidenceSnippet]) -> None:
        self.snippets = snippets
        self._by_reference = {snippet.reference: snippet for snippet in snippets}

    def resolve(self, reference: str) -> EvidenceSnippet:
        try:
            return self._by_reference[reference]
        except KeyError as exc:
            raise ApiError(
                "ANALYSIS_VALIDATION_FAILED",
                "Rule evidence reference does not resolve locally.",
                status_code=422,
                details={"evidence": reference},
            ) from exc

    def references(self) -> list[str]:
        return list(self._by_reference)


class EvidenceIndexer:
    def build(self, documents: dict[str, str]) -> EvidenceIndex:
        snippets: list[EvidenceSnippet] = []
        for doc_id, text in documents.items():
            chunks = self._chunks(text)
            if not chunks:
                raise ApiError(
                    "EMPTY_DOCUMENT",
                    "Extracted text is empty and cannot be analyzed.",
                    status_code=400,
                    details={"doc_id": doc_id},
                )
            for index, chunk in enumerate(chunks, start=1):
                snippet_id = f"s{index:03d}"
                snippets.append(
                    EvidenceSnippet(
                        doc_id=doc_id,
                        snippet_id=snippet_id,
                        reference=f"{doc_id}#{snippet_id}",
                        text=chunk[:500],
                    )
                )
        return EvidenceIndex(snippets)

    @staticmethod
    def _chunks(text: str) -> list[str]:
        normalized = text.strip()
        if not normalized:
            return []
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
        if len(paragraphs) == 1:
            paragraphs = [
                part.strip()
                for part in re.split(r"(?<=[.!?])\s+", normalized)
                if part.strip()
            ]
        return paragraphs[:12]
