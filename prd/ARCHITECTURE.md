# Hermes Writer MVP Architecture

## Scope

This document defines the Phase 2 MVP architecture for Hermes Writer only. It follows the PRD, PRD amendments, and Phase 2 blocker remediation as the source of truth.

No implementation code is included. The MVP remains local-first, single-user, file-backed, and governed by explicit user approval.

## System Topology

```text
React/Vite UI
http://localhost:5173
  -> HTTP JSON and multipart requests
FastAPI backend
http://localhost:8000
  -> local filesystem
  -> LiteLLM proxy only
LiteLLM proxy
  -> Ollama or selected hosted providers
```

FastAPI does not serve React during development. CORS allows `http://localhost:5173` only for the development frontend.

Hermes Writer never calls model providers directly. All model access goes through LiteLLM using OpenAI-compatible requests.

## Backend Module Structure

```text
backend/
  hermes_writer/
    api/
      routes/
        health
        profiles
        documents
        analyses
        skills
        outputs
        config
      schemas
      errors
      cors
    config/
      settings
      provider_config
      privacy_config
    storage/
      path_registry
      atomic_writer
      file_lock
      profile_store
      document_store
      skill_store
      version_store
      output_store
    extraction/
      document_parser
      pdf_extractor
      docx_extractor
      txt_extractor
    analysis/
      style_analyser
      evidence_indexer
      rule_extractor
      rule_validator
      rule_provenance
    skills/
      skill_builder
      skill_registry
      lifecycle
      versioning
      rollback
    llm/
      litellm_client
      provider_router
      prompt_builder
      privacy_guard
      redactor
    generation/
      generation_engine
      rewrite_engine
      output_writer
    audit/
      audit_logger
      event_types
    safety/
      path_safety
      upload_validation
      secret_redaction
      log_sanitizer
```

Key ownership:

* `api` owns request validation, response envelopes, status codes, and API-only DTOs.
* `storage` owns canonical paths, atomic writes, file locks, and local file reads.
* `analysis` owns evidence-based rule extraction and rule provenance.
* `skills` owns lifecycle transitions, immutable versions, active skill selection, and rollback.
* `llm` owns LiteLLM-only calls, privacy-mode routing, provider fallback rules, and prompt filtering.
* `generation` owns write/rewrite orchestration and output persistence.
* `audit` owns append-only JSONL event recording.
* `safety` owns cross-cutting validation for paths, uploads, logs, and secrets.

## Frontend Route Structure

```text
/
  Home/ProfileSelector
/profiles/:profileId
  ProfileDashboard
/profiles/:profileId/documents/upload
  DocumentUploadPage
/profiles/:profileId/documents/:docId
  DocumentPreviewPage
/profiles/:profileId/analyze
  StyleAnalysisPage
/profiles/:profileId/analyses/:analysisId/review
  RuleReviewPage
/profiles/:profileId/skills/:skillId/approval
  SkillApprovalPage
/profiles/:profileId/skills/:skillId/versions
  VersionHistoryPage
/profiles/:profileId/skills/:skillId/audit
  AuditLogPage
/profiles/:profileId/write
  WriteRewritePage
/profiles/:profileId/outputs/:outputId
  OutputDetailPage
/settings
  SettingsPage
```

## Frontend Component Structure

```text
frontend/src/
  api/
    client
    profilesApi
    documentsApi
    analysesApi
    skillsApi
    outputsApi
    configApi
  routes/
    Home
    ProfileDashboard
    DocumentUploadPage
    DocumentPreviewPage
    StyleAnalysisPage
    RuleReviewPage
    SkillApprovalPage
    VersionHistoryPage
    AuditLogPage
    WriteRewritePage
    OutputDetailPage
    SettingsPage
  components/
    layout/
      AppShell
      Header
      StatusBanner
    profiles/
      ProfileSelector
      ProfileForm
      ProfileSummary
    documents/
      UploadDropzone
      ExtractionProgress
      ExtractedTextPreview
      DocumentList
    rules/
      RuleCard
      EvidenceList
      RuleDecisionControls
      RuleEditModal
      CustomRuleModal
    skills/
      SkillCard
      SkillJsonPreview
      LifecycleBadge
      VersionTimeline
      RollbackDialog
    generation/
      SkillSelector
      WriteForm
      RewriteForm
      GenerationProgress
      OutputEditor
      DiffViewer
    settings/
      PrivacyModeSelector
      ProviderStatusList
      StorageLocationPanel
  hooks/
    useProfiles
    useDocuments
    useAnalysis
    useSkills
    useGeneration
    useConfig
  types/
    api
    lifecycle
    privacy
```

The UI must make local storage paths, privacy mode, provider route, skill version, and lifecycle state visible at the point where they affect user trust.

## Canonical File Store Structure

```text
data/
  .version
  profiles/
    {profile_id}/
      profile.json
      documents/
        original/
          {filename}
        extracted/
          {doc_id}.txt
        metadata/
          {doc_id}.json
      skills/
        {skill_id}/
          skill.json
          metadata.json
          versions/
            v{N}.skill.json
          audit/
            audit.jsonl
          outputs/
            draft-{id}.md
            rewrite-{id}.md
```

Canonical paths:

| Item               | Path                                                                    |
| ------------------ | ----------------------------------------------------------------------- |
| Profile            | `data/profiles/{profile_id}/profile.json`                               |
| Original documents | `data/profiles/{profile_id}/documents/original/{filename}`              |
| Extracted text     | `data/profiles/{profile_id}/documents/extracted/{doc_id}.txt`           |
| Document metadata  | `data/profiles/{profile_id}/documents/metadata/{doc_id}.json`           |
| Active skill copy  | `data/profiles/{profile_id}/skills/{skill_id}/skill.json`               |
| Skill versions     | `data/profiles/{profile_id}/skills/{skill_id}/versions/v{N}.skill.json` |
| Version metadata   | `data/profiles/{profile_id}/skills/{skill_id}/metadata.json`            |
| Audit log          | `data/profiles/{profile_id}/skills/{skill_id}/audit/audit.jsonl`        |
| Outputs            | `data/profiles/{profile_id}/skills/{skill_id}/outputs/`                 |

Storage invariants:

* All writes use temp-file plus atomic rename.
* Writes to skill, version, metadata, and audit files use file locking.
* All paths are resolved through a centralized path registry.
* User-controlled path segments are slugged, normalized, and checked against traversal.
* Version files are immutable after creation.
* Historical truth is stored in `versions/*.skill.json`.
* Operational truth is exposed through `skill.json`.
* `skill.json` is a copy of the currently active usable version, not the source of historical truth.
* Rollback validation always reads from immutable version files, never from `skill.json`.
* `metadata.json` is canonical for version index, current version pointer, version statuses, timestamps, change summaries, and rollback metadata.
* Audit logs record events only and are not used to reconstruct rollback state.

## Skill Lifecycle

Canonical statuses:

```text
PENDING -> APPROVED -> ACTIVE -> SUPERSEDED

Rollback copy-forwards a selected historical version into a new immutable version.
The new version is created with status ROLLED_BACK and then becomes the active skill copy.
```

Status meanings:

| Status        | Meaning                                                                                                   |
| ------------- | --------------------------------------------------------------------------------------------------------- |
| `PENDING`     | Proposed skill version exists but has not been approved by the user. It cannot be used for write/rewrite. |
| `APPROVED`    | User approved the version's rules. It is eligible for activation but is not automatically active.         |
| `ACTIVE`      | The version is the current usable skill for generation and rewrite.                                       |
| `SUPERSEDED`  | The version was replaced by a later active version and remains recoverable.                               |
| `ROLLED_BACK` | A new copy-forward version was created from an earlier version and activated after user confirmation.     |

Allowed transitions:

| From               | To                        | Trigger                                                          | Required actor                               |
| ------------------ | ------------------------- | ---------------------------------------------------------------- | -------------------------------------------- |
| none               | `PENDING`                 | Proposed skill created from reviewed rules                       | system after user submits reviewed decisions |
| `PENDING`          | `APPROVED`                | User approves proposed skill version                             | user                                         |
| `APPROVED`         | `ACTIVE`                  | User activates approved version                                  | user                                         |
| `ACTIVE`           | `SUPERSEDED`              | Another approved or rollback version becomes active              | system as part of activation                 |
| historical version | new `ROLLED_BACK` version | User copy-forwards selected version into a new immutable version | user                                         |

Important rollback rule:

```text
Historical Version
  -> copy-forward
New Version with status ROLLED_BACK
  -> activated as skill.json
```

The source version keeps its existing status. An existing `ACTIVE` or `SUPERSEDED` version is never edited in place and never converted into `ROLLED_BACK`.

No skill becomes active automatically. The frontend may offer a single confirmation flow, but the backend must still record approval and activation as explicit lifecycle events.

## Immutable Versioning

Each approved or rollback change creates a new immutable version file:

```text
versions/v1.skill.json
versions/v2.skill.json
versions/v3.skill.json
```

Versioning rules:

* Version numbers only increase.
* Existing `v{N}.skill.json` files are never edited in place.
* `metadata.json` records current version, version list, statuses, change summaries, rollback metadata, and timestamps.
* `skill.json` is updated only after the new immutable version file and metadata are valid.
* Generation and rewrite store the exact `skill_version` used.

## Copy-Forward Rollback

Rollback never rewrites an older version and never restores from audit logs.

Rollback flow:

1. User selects a source version and provides a rollback reason.
2. Backend validates the source version file exists and matches the skill schema.
3. Backend creates a new incremented version copied from the source version.
4. New version status is `ROLLED_BACK`.
5. New version records `rolled_back_from_version`, `rollback_reason`, and rollback timestamp.
6. Previous `ACTIVE` version becomes `SUPERSEDED`.
7. Source version keeps its previous status and remains immutable.
8. New `ROLLED_BACK` version becomes the active `skill.json` copy after user confirmation.
9. `metadata.json` records the new current version and rollback metadata.
10. Audit log records the rollback event.

## Evidence-Based Rule Extraction

Rule extraction must be evidence-first, not preference guessing.

Core entities:

| Entity         | Purpose                                                                     |
| -------------- | --------------------------------------------------------------------------- |
| Evidence index | Local map of document IDs, snippet IDs, offsets, and short source snippets. |
| Candidate rule | Draft rule with category, description, confidence, and source references.   |
| User decision  | Approve, reject, edit, or add custom rule.                                  |
| Skill rule     | Approved rule persisted into a skill version with provenance.               |

Rule provenance:

| Source             | Evidence                                                                         |
| ------------------ | -------------------------------------------------------------------------------- |
| `document_derived` | Required. At least one source reference such as `doc_id#snippet_id`.             |
| `user_authored`    | Must be `null`. The rule is explicit user input, not inferred document evidence. |

Extraction architecture:

* Document parsing stores extracted text locally before analysis.
* Evidence indexing happens locally and creates snippet references.
* Local Only analysis may include raw extracted text and source snippets in prompts routed to Ollama through LiteLLM.
* Hybrid and Cloud Allowed hosted-provider prompts must not include raw uploaded document text or source snippets.
* If hosted providers are used during analysis, they may receive only abstractions, summaries, approved rules, and non-raw metadata.
* Backend validation rejects any document-derived rule without evidence references.
* Backend validation rejects any rule whose evidence reference does not resolve to a local source snippet.
* The UI shows evidence snippets locally for user review, regardless of whether a hosted provider assisted with non-raw abstraction.

Because hosted providers cannot see raw documents in MVP privacy rules, Local Only Ollama is the preferred and required route for full document-derived rule extraction from raw text. Hosted models may only assist after local abstraction and must not become the sole authority for document-derived evidence.

## User Approval Before Activation

The approval boundary is part of the product, not optional UX.

Required approval gates:

1. User previews extracted text before it is eligible for analysis.
2. User reviews rule cards with evidence.
3. User approves, rejects, edits, or adds rules.
4. Backend creates a `PENDING` skill candidate from the reviewed rule set.
5. User approves the skill version, moving it to `APPROVED`.
6. User activates the approved version, moving it to `ACTIVE`.

Write and rewrite endpoints only accept skills whose current usable version is `ACTIVE` or a copy-forward `ROLLED_BACK` version that has been activated as `skill.json`.

## LiteLLM-Only Provider Routing

All LLM operations go through:

```text
Hermes backend -> LiteLLM proxy -> selected provider
```

Provider routing module responsibilities:

* Resolve operation type: analysis, write, rewrite, provider test.
* Resolve privacy mode: `local_only`, `hybrid`, `cloud_allowed`.
* Resolve allowed providers for the selected mode.
* Build a LiteLLM request only after privacy guard approval.
* Reject direct provider URLs, SDK clients, or provider-specific calls outside LiteLLM.
* Record provider, model, privacy mode, and operation ID in audit-safe logs without raw prompts.

Provider configuration:

* Provider credentials live in `.env`.
* The UI may display configured/not configured status.
* The UI must not write provider credentials through an unauthenticated local API.
* Cloud provider availability is optional for MVP startup.
* Local Only startup requires routing rules to exist, but analysis/generation fails closed if Ollama is unavailable at operation time.

## Privacy Modes

| Mode          | API value       | Allowed providers                                            | Raw uploaded document text                          | Hosted fallback                     |
| ------------- | --------------- | ------------------------------------------------------------ | --------------------------------------------------- | ----------------------------------- |
| Local Only    | `local_only`    | Ollama only through LiteLLM                                  | Allowed only to local Ollama                        | Never                               |
| Hybrid        | `hybrid`        | Ollama first, selected hosted providers after user selection | Never to hosted providers                           | Controlled, user-selected           |
| Cloud Allowed | `cloud_allowed` | Selected hosted providers through LiteLLM                    | Never as raw snippets or raw uploaded document text | Permitted within selected providers |

Default mode is Local Only.

Local Only fail-closed rules:

* If requested provider is not Ollama, reject before calling LiteLLM.
* If Ollama is unavailable, return a provider-unavailable error and do not fallback.
* If LiteLLM routing would select any hosted provider, block the operation.
* Analysis, write, and rewrite all use the same fail-closed guard.

Hosted-provider prompt rules:

* Allowed: approved style rules, abstractions, summaries, document type, user-provided write prompt, user-provided rewrite input, and user instructions.
* Forbidden: raw uploaded document text, stored extracted text, source snippets, evidence excerpts, full prompts in logs, API keys.

## Audit Logging

Audit logs are append-only JSONL at:

```text
data/profiles/{profile_id}/skills/{skill_id}/audit/audit.jsonl
```

Required event categories:

* `document_uploaded`
* `document_extracted`
* `analysis_started`
* `analysis_completed`
* `rule_approved`
* `rule_rejected`
* `custom_rule_added`
* `skill_created`
* `skill_approved`
* `skill_activated`
* `skill_superseded`
* `skill_rollback`
* `draft_generated`
* `rewrite_generated`
* `skill_deleted`

Audit safety:

* Logs include IDs, timestamps, actor, operation type, lifecycle transition, provider name, model name, and file paths.
* Logs do not include raw uploaded document text, evidence snippets, full prompts, generated full outputs, secrets, or API keys.
* Audit entries are append-only and are never edited to change history.
* Rollback uses immutable version files; audit logs only record that rollback occurred.

## API Boundary

Base backend URL:

```text
http://localhost:8000
```

Frontend URL:

```text
http://localhost:5173
```

API conventions:

* JSON response envelope with success data or error code/message.
* Multipart only for document upload.
* All other mutating requests use JSON.
* Request validation happens at the API boundary.
* Backend returns structured errors with recovery hints for configuration, extraction, provider, privacy, and storage failures.
* API response bodies must not expose stack traces, filesystem internals beyond approved canonical paths, secrets, or raw prompt logs.

Endpoint groups:

| Group     | Boundary                                                     |
| --------- | ------------------------------------------------------------ |
| Health    | `GET /health`, `GET /api/status`                             |
| Profiles  | create, list, read, update, soft delete profiles             |
| Documents | upload, list, read, update extracted text, delete            |
| Analysis  | start style analysis, poll status, submit rule decisions     |
| Skills    | list, read, approve, activate, versions, rollback, audit     |
| Outputs   | write, rewrite, generation status, list outputs, read output |
| Config    | read config, update privacy mode, test provider              |

Important API corrections from PRD precedence:

* Skill approval must not silently activate a skill.
* Activation requires explicit user intent.
* There is no login/auth API in MVP.
* There is no credential-write API in MVP.
* There are no database or migration endpoints in MVP.

## Operation Flows

### Create Skill

```text
Create/select profile
  -> upload documents
  -> extract text locally
  -> preview/edit extracted text
  -> choose privacy mode and provider route
  -> analyze style through privacy guard and LiteLLM
  -> create local evidence index
  -> validate document-derived rules have evidence
  -> user reviews rules
  -> user submits decisions
  -> create PENDING skill
  -> user approves skill
  -> create immutable version
  -> user activates approved version
  -> update skill.json active copy
  -> update metadata.json version index
  -> append audit events
```

### Write

```text
User selects ACTIVE skill
  -> backend loads skill.json and exact version
  -> privacy guard resolves provider route
  -> prompt builder includes allowed style rules
  -> LiteLLM call
  -> output saved as draft-{id}.md
  -> audit event records skill version and provider metadata
```

### Rewrite

```text
User selects ACTIVE skill and supplies current text
  -> backend loads skill.json and exact version
  -> privacy guard resolves provider route
  -> prompt builder includes allowed style rules and user rewrite input
  -> hosted prompts exclude stored source snippets
  -> LiteLLM call
  -> output saved as rewrite-{id}.md
  -> audit event records skill version and provider metadata
```

## Safety Gates Before Sprint 1 Implementation

Sprint 1 must not begin until these architecture gates are accepted:

| Gate            | Requirement                                                                                                                  |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| PRD compliance  | Architecture explicitly excludes SQL, login/auth, cloud database, direct provider calls, and automatic learning.             |
| Canonical paths | Storage path registry is planned around the exact PRD amendment paths, including `metadata.json` for skill version metadata. |
| Lifecycle       | Only `PENDING`, `APPROVED`, `ACTIVE`, `SUPERSEDED`, `ROLLED_BACK` are allowed.                                               |
| Approval        | No transition to `ACTIVE` without explicit user activation.                                                                  |
| LiteLLM-only    | All model operations route through LiteLLM; direct SDK/provider calls are disallowed.                                        |
| Privacy         | Local Only fail-closed routing exists before analysis can be implemented.                                                    |
| Evidence        | Document-derived rules require local evidence references; user-authored rules use `evidence: null`.                          |
| Cloud filtering | Hosted-provider prompts never receive raw uploaded document text or evidence snippets.                                       |
| Versioning      | Version files are immutable; rollback is copy-forward only.                                                                  |
| Audit           | Audit log is append-only and contains no raw private text or secrets.                                                        |
| API boundary    | React/Vite and FastAPI remain separate services with CORS for `localhost:5173`.                                              |
| Testing         | Sprint 1 scaffolding includes backend, frontend, integration, privacy, path, and safety test harnesses.                      |

## Required Tests Planned Before Sprint 1

These test categories must be scaffolded in Sprint 1 and filled as modules land:

* Storage path contract tests for every canonical path.
* Atomic write and partial-write recovery tests.
* Path traversal and malicious filename rejection tests.
* CORS allowed-origin and rejected-origin tests.
* API envelope and error response tests.
* Config validation tests with recovery hints.
* Lifecycle transition tests using only canonical statuses.
* LiteLLM-only boundary tests that fail if a direct provider client is introduced.
* Local Only fail-closed routing tests for analysis, write, and rewrite.
* Hosted-provider prompt filtering tests for raw document text and evidence snippets.
* Rule provenance tests for `document_derived` and `user_authored`.
* Immutable versioning and copy-forward rollback tests.
* Rollback validation tests confirming source versions remain unchanged.
* `metadata.json` version-index tests.
* Audit log append-only and secret/raw-text redaction tests.
* Frontend component tests for approval gates, privacy selector, rule review, and version history.

## Required Planning Synchronisation

Because this architecture makes `data/profiles/{profile_id}/skills/{skill_id}/metadata.json` canonical for version metadata, the following planning files must also include that path and its tests before Sprint 1 starts:

* `prd/STORAGE_MODEL.md`
* `prd/API_PLAN.md`
* `prd/TESTING_PLAN.md`
* `prd/ACCEPTANCE_CRITERIA.md`
* `prd/DETAILED_SPRINTS.md`

At minimum, each file must state that `metadata.json` records:

* current version
* version list
* lifecycle status per version
* creation timestamps
* change summaries
* rollback source version
* rollback reason
* rollback timestamp

## MVP Exclusions

The MVP architecture intentionally excludes:

* SQL databases.
* Cloud databases or cloud file storage.
* Login, auth, sessions, JWTs, teams, or collaboration.
* Credential mutation through the app UI/API.
* Direct provider SDK calls outside LiteLLM.
* Raw uploaded document text or evidence snippets sent to hosted providers.
* Automatic continuous learning.
* Fine-tuning.
* Real-time collaborative editing.