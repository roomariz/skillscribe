# Phase 2 Blocker Remediation

## Scope

This correction pass updates the planning package only. No implementation code was added.

Source of truth remains the PRD, with explicit PRD amendments added for rollback copy-forward semantics, canonical storage paths, privacy routing, and custom rule provenance.

## Remediated Issues

### HW-AUD-001: Canonical Status Lifecycle

Files changed:
- `prd/local-first-personal-writing-skill-assistant.md`
- `prd/API_PLAN.md`
- `prd/STORAGE_MODEL.md`
- `prd/DETAILED_SPRINTS.md`
- `prd/UI_PLAN.md`
- `prd/TESTING_PLAN.md`
- `prd/ACCEPTANCE_CRITERIA.md`

Exact correction:
- Standardized skill lifecycle to `PENDING`, `APPROVED`, `ACTIVE`, `SUPERSEDED`, `ROLLED_BACK`.
- Removed non-canonical lifecycle status values from active planning.
- Added lifecycle diagrams and transition tables in PRD, API Plan, and Storage Model.

Reason:
- API, storage, UI, tests, and acceptance criteria previously used incompatible status values.

Verification performed:
- Searched for non-canonical lifecycle status values.

### HW-AUD-002 / HW-AUD-003 / HW-AUD-004 / HW-AUD-005: Canonical Storage Paths

Files changed:
- `prd/local-first-personal-writing-skill-assistant.md`
- `prd/API_PLAN.md`
- `prd/STORAGE_MODEL.md`
- `prd/DETAILED_SPRINTS.md`
- `prd/UI_PLAN.md`
- `prd/TESTING_PLAN.md`
- `prd/ACCEPTANCE_CRITERIA.md`

Exact correction:
- Audit log path standardized to `data/profiles/{profile_id}/skills/{skill_id}/audit/audit.jsonl`.
- Outputs standardized under `data/profiles/{profile_id}/skills/{skill_id}/outputs/`.
- Document metadata standardized to `data/profiles/{profile_id}/documents/metadata/{doc_id}.json`.
- Output filenames standardized to `draft-{id}.md` and `rewrite-{id}.md`.
- Added storage path consistency tables in PRD, Storage Model, API Plan, and Testing Plan.

Reason:
- Planning documents disagreed on audit, output, and metadata locations.

Verification performed:
- Searched for obsolete paths: `data/profiles/{profile_id}/outputs`, `documents/{doc_id}/meta`, `skills/{skill_id}/audit.jsonl`.

### HW-AUD-006: PDF Extraction Standardization

Files changed:
- `prd/API_PLAN.md`
- `prd/STORAGE_MODEL.md`
- `prd/DETAILED_SPRINTS.md`
- `prd/RISKS.md`
- `prd/TESTING_PLAN.md`
- `prd/ACCEPTANCE_CRITERIA.md`

Exact correction:
- Standardized PDF extraction on PyMuPDF.
- Updated extraction metadata to `"extraction_method": "pymupdf"`.
- Removed non-PyMuPDF PDF extraction libraries from MVP planning.

Reason:
- PRD specified PyMuPDF, while downstream plans used non-canonical PDF extraction libraries.

Verification performed:
- Searched for non-canonical PDF extraction library references.

### HW-AUD-007: Frontend / Backend Topology

Files changed:
- `prd/API_PLAN.md`
- `prd/DETAILED_SPRINTS.md`
- `prd/ACCEPTANCE_CRITERIA.md`

Exact correction:
- Standardized development topology:
  - React/Vite frontend: `http://localhost:5173`
  - FastAPI backend: `http://localhost:8000`
  - FastAPI does not serve React during development.
- Added architecture diagram in API Plan.
- Acceptance Criteria now require CORS for `http://localhost:5173`.

Reason:
- Previous criteria simultaneously required separate Vite serving and FastAPI-served React.

Verification performed:
- Searched for `Serves React`, `proxied`, and contradictory serving language.

### HW-AUD-008 / HW-AUD-009 / HW-AUD-010: Privacy Mode Enforcement and Sequencing

Files changed:
- `prd/local-first-personal-writing-skill-assistant.md`
- `prd/API_PLAN.md`
- `prd/DETAILED_SPRINTS.md`
- `prd/UI_PLAN.md`
- `prd/RISKS.md`
- `prd/TESTING_PLAN.md`
- `prd/ACCEPTANCE_CRITERIA.md`
- `prd/sprints.md`

Exact correction:
- Standardized privacy modes:
  - Local Only: Ollama only; fail closed.
  - Hybrid: Ollama first; controlled hosted fallback after user selection.
  - Cloud Allowed: selected hosted providers permitted through LiteLLM.
- Added explicit routing matrices.
- Reordered Sprint 3 so privacy/provider routing exists before style analysis.
- Updated Sprint 5 to configure and verify already-enforced privacy behavior.

Reason:
- Local Only previously allowed cloud fallback in several documents, and style analysis could occur before privacy controls existed.

Verification performed:
- Searched for `ollama_only`, `Ollama-only`, `Ollama + Fallback`, `Cloud-only`, and unqualified cloud fallback references.

### HW-AUD-011: Evidence Snippet Leakage

Files changed:
- `prd/local-first-personal-writing-skill-assistant.md`
- `prd/API_PLAN.md`
- `prd/DETAILED_SPRINTS.md`
- `prd/RISKS.md`
- `prd/TESTING_PLAN.md`
- `prd/ACCEPTANCE_CRITERIA.md`

Exact correction:
- Local Only may use source snippets locally.
- Hybrid and Cloud Allowed must not send raw document snippets to hosted providers.
- Hosted provider prompts may include approved style rules, abstractions, summaries, and user prompts.
- Added privacy test requirements for snippet filtering.

Reason:
- Evidence snippets are raw document excerpts and can leak private content.

Verification performed:
- Searched for prompt instructions that unconditionally included evidence snippets.

### HW-AUD-012 / HW-AUD-013 / HW-AUD-016: Excluded Scope and Credential Safety

Files changed:
- `prd/API_PLAN.md`
- `prd/STORAGE_MODEL.md`
- `prd/DETAILED_SPRINTS.md`
- `prd/UI_PLAN.md`

Exact correction:
- Removed future JWT/session authentication language from API Plan.
- Removed SQL migration and replication language from Storage Model MVP planning.
- Removed credential-write API planning; provider keys remain `.env` configuration.
- UI now shows cloud provider keys as configured in `.env` rather than saved through the app.

Reason:
- MVP excludes login, SQL databases, cloud database/storage expansion, and unsafe credential mutation through unauthenticated local APIs.

Verification performed:
- Searched for `JWT`, `session-based auth`, `SQLite`, `PostgreSQL backend`, `Replication`, and `POST /api/config/add-api-key`.

### HW-AUD-014 / HW-AUD-015: LiteLLM and API Consistency

Files changed:
- `prd/API_PLAN.md`
- `prd/DETAILED_SPRINTS.md`

Exact correction:
- API Plan clarifies FastAPI sends OpenAI-compatible requests to LiteLLM proxy.
- Detailed Sprints require provider calls through LiteLLM only.
- Added missing `POST /api/config/update-privacy-mode` endpoint to API Plan.

Reason:
- Plans were ambiguous about direct provider routing and contained sprint endpoints absent from the API contract.

Verification performed:
- Reviewed API Plan and Detailed Sprints for LiteLLM-only routing consistency.

### HW-AUD-017 / HW-AUD-018: Custom Rule Provenance

Files changed:
- `prd/local-first-personal-writing-skill-assistant.md`
- `prd/API_PLAN.md`
- `prd/STORAGE_MODEL.md`
- `prd/UI_PLAN.md`
- `prd/DETAILED_SPRINTS.md`
- `prd/ACCEPTANCE_CRITERIA.md`

Exact correction:
- Kept custom rules but marked them as:
  - `source: "user_authored"`
  - `evidence: null`
- Document-derived rules use:
  - `source: "document_derived"`
  - evidence references.
- Changed PRD safety rule to prohibit document-derived rules without evidence.
- Replaced numeric rule quota with evidence-based acceptance.

Reason:
- Custom rules are user governance input, not inferred document evidence. Numeric quotas encouraged hallucinated rules.

Verification performed:
- Reviewed rule schemas and acceptance criteria for provenance fields.

### HW-AUD-019 / HW-AUD-020: Sprint and Provider Consistency

Files changed:
- `prd/sprints.md`
- `prd/DETAILED_SPRINTS.md`
- `prd/RISKS.md`
- `prd/API_PLAN.md`

Exact correction:
- Sprint 3 now includes privacy routing before style analysis.
- Sprint 5 now focuses on provider configuration and privacy settings verification.
- Provider sets are described as selected providers through LiteLLM, with Local Only restricted to Ollama.

Reason:
- Previous sprint order allowed model calls before privacy mode enforcement.

Verification performed:
- Reviewed sprint summary and detailed sprint ordering.

### HW-AUD-021 / HW-AUD-022 / HW-AUD-023 / HW-AUD-024 / HW-AUD-025 / HW-AUD-026: Acceptance and Testing Hardening

Files changed:
- `prd/TESTING_PLAN.md`
- `prd/ACCEPTANCE_CRITERIA.md`
- `prd/DETAILED_SPRINTS.md`

Exact correction:
- Added tests for:
  - storage path contracts
  - Local Only fail-closed routing
  - cloud fallback restrictions
  - evidence snippet filtering
  - rollback lifecycle
  - path traversal attacks
  - malicious filenames
  - CORS restrictions
  - secret leakage prevention
- Replaced subjective final criteria with measurable thresholds and checklists.
- Made cloud credentials optional `.env` configuration, not required for local-only startup.

Reason:
- Previous acceptance criteria were partly subjective and did not cover critical privacy/security/path risks.

Verification performed:
- Reviewed Testing Plan and Acceptance Criteria for each required hardening item.

### HW-AUD-029: Rollback Model

Files changed:
- `prd/local-first-personal-writing-skill-assistant.md`
- `prd/API_PLAN.md`
- `prd/STORAGE_MODEL.md`
- `prd/DETAILED_SPRINTS.md`
- `prd/TESTING_PLAN.md`
- `prd/ACCEPTANCE_CRITERIA.md`

Exact correction:
- Standardized rollback as copy-forward rollback.
- Rollback creates a new immutable version with:
  - incremented version number
  - status `ROLLED_BACK`
  - `rolled_back_from_version`
- Added rollback lifecycle examples in PRD and Storage Model.

Reason:
- PRD previously described pointer rollback while other plans described copying.

Verification performed:
- Searched for old pointer-only rollback language and reviewed rollback sections.

## Verification Summary

Searches performed:
- Old lifecycle values: non-canonical lifecycle status references.
- Old PDF libraries: non-canonical PDF extraction references.
- Old privacy labels: `ollama_only`, `Ollama-only`, `Ollama + Fallback`, `Cloud-only`.
- Old paths: `data/profiles/{profile_id}/outputs`, `documents/{doc_id}/meta`, `skills/{skill_id}/audit.jsonl`.
- Excluded scope markers: `JWT`, `session-based auth`, `SQLite`, `PostgreSQL backend`, `Replication`.
- Contradictory topology markers: `Serves React`, `proxied`, development FastAPI-served React language.

## Final Consistency Audit

| Area | Status | Notes |
|------|--------|-------|
| Lifecycle | PASS | Canonical lifecycle is used for skill statuses. |
| Storage paths | PASS | Canonical audit, output, metadata, skill, and version paths are documented. |
| PDF extraction | PASS | PyMuPDF is the sole PDF extraction library; metadata uses `pymupdf`. |
| Privacy modes | PASS | Local Only, Hybrid, and Cloud Allowed are defined with routing matrix. |
| Rollback model | PASS | Copy-forward rollback is documented consistently. |
| API consistency | PASS | API Plan includes lifecycle, routing, storage paths, topology, and privacy update endpoint. |
| UI consistency | PASS | UI labels match canonical privacy modes and paths. |
| Testing consistency | PASS | Required blocker tests are listed. |
| PRD compliance | PASS | No SQL, login, cloud database, collaboration, fine-tuning, or continuous learning was added to MVP scope. |

Overall result: PASS.

## Final Targeted Remediation

### P2-001 fixed

File changed:
- `prd/DETAILED_SPRINTS.md`

Exact correction:
- Replaced relative-only document metadata, audit log, and output paths with exact canonical `data/profiles/{profile_id}/...` paths.

Verification performed:
- Searched `prd/DETAILED_SPRINTS.md` for remaining relative-only metadata, audit, and output path references.

### P2-002 fixed

File changed:
- `prd/PHASE2_BLOCKER_REMEDIATION.md`

Exact correction:
- Removed banned historical PDF library names from the active remediation report.
- Kept PyMuPDF as the sole PDF extraction library and `pymupdf` as the metadata value.

Verification performed:
- Searched active planning documents for banned PDF library names.

### P2-003 fixed

File changed:
- `prd/ACCEPTANCE_CRITERIA.md`

Exact correction:
- Added Sprint 3 acceptance criteria requiring provider routing, privacy mode selection, Local Only fail-closed behavior, non-Ollama rejection in Local Only, and active privacy enforcement before style analysis can run.

Verification performed:
- Reviewed Sprint 3 ordering to confirm provider routing and privacy enforcement precede style analysis.

### P2-004 fixed

File changed:
- `prd/ACCEPTANCE_CRITERIA.md`

Exact correction:
- Updated write, rewrite, and prompt-engineering criteria so Local Only may use raw text and source snippets through Ollama only.
- Restricted Hybrid and Cloud Allowed hosted-provider prompts to approved style rules, abstractions, summaries, and user-provided generation or rewrite instructions.
- Required hosted-provider rewrite prompts to exclude stored source document snippets.

Verification performed:
- Searched acceptance criteria for unqualified prompt, evidence snippet, and raw-text leakage language.

### P2-005 fixed

Files changed:
- `prd/RISKS.md`
- `prd/TESTING_PLAN.md`

Exact correction:
- Replaced audit-log restoration language with copy-forward rollback from immutable version files.
- Stated that audit logs record rollback events only.
- Added required rollback metadata checks for `status = ROLLED_BACK`, `rolled_back_from_version`, `rollback_reason`, and rollback timestamp.

Verification performed:
- Searched active planning documents for audit-log file restoration wording.

### P2-006 fixed

File changed:
- `prd/ACCEPTANCE_CRITERIA.md`

Exact correction:
- Replaced subjective acceptance wording with measurable criteria for extraction, rule schema compliance, source references, provider error responses, rollback metadata, and PRD checklist completion.

Verification performed:
- Searched acceptance criteria for the previously flagged subjective phrases.
