# Acceptance Criteria

## Sprint 1: Project Scaffold & Local Storage

### AC 1.1: FastAPI Backend Runs Locally
- [ ] FastAPI server starts without errors on `localhost:8000`
- [ ] Health check endpoint `GET /health` returns `{"status": "ok"}`
- [ ] FastAPI does not serve React during development
- [ ] CORS allows the development frontend origin `http://localhost:5173`
- [ ] All endpoints return proper JSON responses
- [ ] Error responses include `error_code` and `message`

### AC 1.2: React/Vite Frontend Loads
- [ ] Vite dev server runs on `localhost:5173`
- [ ] Frontend builds without errors (`npm run build`)
- [ ] Build output is < 500KB (JavaScript + CSS combined, gzipped)
- [ ] No TypeScript compilation errors
- [ ] Webpack/Vite bundle analysis included

### AC 1.3: Local File Store Initialized
- [ ] On first startup, creates `./data/` directory structure
- [ ] `data/profiles/` directory exists and is writable
- [ ] Atomic file writes with temporary file + rename
- [ ] No file corruption on abrupt shutdown
- [ ] Backup of existing data before modifications

### AC 1.4: Configuration Management
- [ ] `.env` file template created (`LiteLLM_API_KEY`, `OLLAMA_BASE_URL`, etc.)
- [ ] Configuration validated on startup
- [ ] Startup failure response includes `error_code: "CONFIG_MISSING"` and `recovery_hint` listing each missing required setting
- [ ] Example config file provided in docs

### AC 1.5: Git & CI/CD Setup
- [ ] `.gitignore` excludes `data/`, `.env`, `node_modules/`, `*.pyc`
- [ ] GitHub Actions workflow runs on push (linting, type check, build)
- [ ] Pre-commit hooks configured (optional)

### AC 1.6: Documentation
- [ ] README includes setup steps (Python env, Node env, LiteLLM)
- [ ] ARCHITECTURE.md explains backend/frontend split
- [ ] Contributor guide for running locally

---

## Sprint 2: Profile Management & Document Handling

### AC 2.1: Profile Creation
- [ ] User can create a profile with name
- [ ] Profile saved to `data/profiles/{profile_id}/profile.json`
- [ ] Unique profile IDs (UUID or slug)
- [ ] Profile UI shows creation timestamp

### AC 2.2: Document Upload
- [ ] User can upload PDF, DOCX, TXT files via drag-and-drop or file picker
- [ ] File size limit enforced (default 50MB)
- [ ] Progress bar shows upload status
- [ ] Uploaded file stored at `data/profiles/{profile_id}/documents/original/{filename}`
- [ ] Original filename and MIME type preserved in metadata

### AC 2.3: Document Extraction
- [ ] PDF extraction uses PyMuPDF and returns non-empty UTF-8 text for valid PDF fixture files
- [ ] PDF extraction preserves paragraph breaks in PDF fixture files
- [ ] DOCX extraction returns non-empty UTF-8 text and preserves paragraph breaks in DOCX fixture files
- [ ] TXT files parsed as-is
- [ ] Extracted text stored at `data/profiles/{profile_id}/documents/extracted/{doc_id}.txt`
- [ ] Extraction failure response includes `error_code: "EXTRACTION_FAILED"` and `recovery_hint`
- [ ] Fallback: user can paste extracted text manually

### AC 2.4: Text Preview
- [ ] UI shows extracted text in read-only editor
- [ ] Preview is live-scrollable and searchable (Ctrl+F)
- [ ] Character count displayed
- [ ] Option to edit extracted text manually before analysis
- [ ] Changes saved if user approves

### AC 2.5: Metadata Storage
- [ ] Document metadata file: `data/profiles/{profile_id}/documents/metadata/{doc_id}.json`
- [ ] Includes: original filename, upload date, extraction date, word count, character count
- [ ] Audit log entry for each upload

---

## Sprint 3: Style Analysis & Rule Extraction

### AC 3.1: Provider Routing & Privacy Enforcement Gate
- [ ] Provider routing is configured before any style analysis request can be accepted
- [ ] Privacy mode is selected and persisted before any style analysis request can be accepted
- [ ] Local Only routes analysis to Ollama only and fails closed when Ollama is unavailable
- [ ] Non-Ollama provider calls are rejected in Local Only with `error_code: "LOCAL_ONLY_PROVIDER_BLOCKED"`
- [ ] Style analysis cannot run until privacy enforcement is active; blocked requests return `error_code: "PRIVACY_ENFORCEMENT_REQUIRED"`

### AC 3.2: Style Analyzer Initialization
- [ ] Backend loads extracted text documents
- [ ] Analyzer request includes the selected privacy mode and resolved provider route
- [ ] Uses LLM (via LiteLLM) to generate style rules only after privacy enforcement passes
- [ ] Local Only analysis may include raw extracted text only in prompts routed to Ollama
- [ ] Hybrid and Cloud Allowed hosted-provider analysis prompts exclude raw source snippets and raw uploaded document text

### AC 3.3: Rule Generation
- [ ] LLM produces JSON rules with structure:
  - `rule_id`, `category` (tone, structure, vocabulary, etc.)
  - `description`, `examples` (positive + negative)
  - `source_snippets` (list of document excerpts that support rule)
- [ ] The analyzer returns zero or more rules; every returned document-derived rule includes evidence and confidence
- [ ] Rules conform to the documented JSON schema
- [ ] Every document-derived rule has at least one source reference and confidence score between 0 and 1

### AC 3.4: Rule Preview & Approval
- [ ] UI shows each rule with evidence snippets
- [ ] User can approve, reject, or edit each rule
- [ ] Rejected rules not included in skill
- [ ] Edited rules stored with user modification note
- [ ] Ability to add custom rules manually
- [ ] Custom rules are stored with `source: "user_authored"` and `evidence: null`

### AC 3.5: Proposed Skill File
- [ ] System generates `skill.json` with approved rules
- [ ] Stored at `data/profiles/{profile_id}/skills/{skill_id}/skill.json`
- [ ] Includes: skill_id, profile_id, name, version, created_at, rules array
- [ ] Skill is read-only until approved

### AC 3.6: Processing Status
- [ ] User sees progress indication during style analysis
- [ ] Estimated time shown if analysis is long
- [ ] Option to cancel analysis (safe rollback)
- [ ] Logs all processing steps in audit file

---

## Sprint 4: Skill Review, Approval & Versioning

### AC 4.1: Skill Approval Workflow
- [ ] User reviews proposed skill JSON
- [ ] Option to approve, reject, or iterate
- [ ] Approved skills move through canonical lifecycle states only: PENDING, APPROVED, ACTIVE, SUPERSEDED, ROLLED_BACK
- [ ] Status stored in skill.json uses uppercase canonical values
- [ ] Approval timestamp and approver recorded

### AC 4.2: Active Skill Registry
- [ ] UI lists all active skills for profile
- [ ] Default skill selectable and persisted in profile.json
- [ ] SUPERSEDED skills remain recoverable through rollback

### AC 4.3: Versioning
- [ ] Each skill change creates new version: `v1.skill.json`, `v2.skill.json`
- [ ] Version history visible in UI
- [ ] Version metadata includes: date, change summary, diff from previous

### AC 4.4: Rollback
- [ ] User can rollback to any previous skill version
- [ ] Rollback is logged in audit log
- [ ] Rollback copies a selected immutable version into a new immutable version
- [ ] New rollback version records `status: "ROLLED_BACK"`, `rolled_back_from_version`, `rollback_reason`, and rollback timestamp

### AC 4.5: Audit Logging
- [ ] `data/profiles/{profile_id}/skills/{skill_id}/audit/audit.jsonl` created
- [ ] Each line is JSON event: `{timestamp, event_type, actor, details}`
- [ ] Event types: `skill_created`, `rule_approved`, `rule_rejected`, `skill_approved`, `skill_rollback`
- [ ] Audit log immutable after write

### AC 4.6: Skill Deletion
- [ ] User can soft-delete skills (marked deleted, not removed)
- [ ] Deletion logged in audit trail
- [ ] Hard delete only after 30-day retention (configurable)

---

## Sprint 5: LiteLLM Integration & Provider Configuration

### AC 5.1: LiteLLM Proxy Integration
- [ ] Backend calls LiteLLM for all LLM operations
- [ ] No direct calls to model providers
- [ ] LiteLLM configured with multiple providers (Ollama, Groq, Mistral, OpenAI)
- [ ] Provider selection configurable in backend

### AC 5.2: Ollama Local Support
- [ ] Detect local Ollama on startup (http://localhost:11434)
- [ ] If available, use Ollama as primary provider (privacy-first)
- [ ] If Ollama is unavailable, Local Only fails closed; Hybrid or Cloud Allowed may use permitted hosted providers
- [ ] User configurable via .env: `OLLAMA_BASE_URL`

### AC 5.3: Privacy Modes
- [ ] Mode 1: Local Only uses Ollama only and fails closed if Ollama is unavailable
- [ ] Mode 2: Hybrid uses Ollama first and may use controlled hosted fallback only after user selection
- [ ] Mode 3: Cloud Allowed permits selected cloud providers
- [ ] User selects mode in UI; persisted in profile
- [ ] Raw document snippets are never sent to hosted providers; cloud requests contain only approved style rules, abstractions, summaries, and user prompts

### AC 5.4: Provider Configuration UI
- [ ] Settings page shows available providers
- [ ] User can configure API keys for cloud providers via `.env` (Groq, Mistral, OpenAI, etc.)
- [ ] Test connection button validates each provider
- [ ] Configuration stored in `.env` (not in user files)

### AC 5.5: Provider Fallback
- [ ] If primary provider fails, fallback is attempted only when the selected privacy mode permits it
- [ ] Retry logic with exponential backoff (3 attempts max)
- [ ] User informed of provider switch
- [ ] Log provider used for each operation

### AC 5.6: Error Handling
- [ ] Provider failure responses include exact `error_code`, `message`, and `recovery_hint`
- [ ] Fallback to local Ollama if cloud provider unavailable
- [ ] Suggest setup steps if no provider available

---

## Sprint 6: Write & Rewrite Workflows

### AC 6.1: Write Workflow
- [ ] User opens "New Document" modal
- [ ] Selects active skill from dropdown
- [ ] Optionally provides writing prompt or outline
- [ ] Clicks "Generate" to create new writing using skill
- [ ] Local Only generation may send raw text and source snippets only to Ollama
- [ ] Hybrid and Cloud Allowed hosted-provider generation prompts contain only approved style rules, abstractions, summaries, and user-provided generation instructions
- [ ] Generated text displayed in editor

### AC 6.2: Write Output Storage
- [ ] Generated document saved under `data/profiles/{profile_id}/skills/{skill_id}/outputs/` as `draft-{id}.md`
- [ ] Metadata includes: skill version used, LLM model, generation date, prompt
- [ ] User can save, edit, or discard output

### AC 6.3: Rewrite Workflow
- [ ] User uploads or pastes existing text
- [ ] Selects active skill
- [ ] Clicks "Rewrite" to apply skill style to text
- [ ] Local Only rewrite may send raw current input text and source snippets only to Ollama
- [ ] Hybrid and Cloud Allowed hosted-provider rewrite prompts contain approved style rules, abstractions, summaries, and the user-provided current rewrite input only
- [ ] Hosted-provider rewrite prompts do not include stored source document snippets
- [ ] Rewritten text displayed with diff view

### AC 6.4: Rewrite Output Storage
- [ ] Rewritten document saved under `data/profiles/{profile_id}/skills/{skill_id}/outputs/` as `rewrite-{id}.md`
- [ ] Original text included in metadata for reference
- [ ] Diff preserved (original + rewritten)

### AC 6.5: LLM Prompt Engineering
- [ ] System prompt explains skill context
- [ ] Skill rules embedded in prompt as bullet points
- [ ] Evidence snippets are included only for Local Only prompts routed to Ollama
- [ ] Hosted-provider prompts contain no raw source snippets and no raw uploaded document text
- [ ] Temperature and other params configurable per skill

### AC 6.6: Output History
- [ ] User sees list of all generated/rewritten documents
- [ ] Can compare versions side-by-side
- [ ] Can export to Markdown, plain text, or copy to clipboard

---

## Sprint 7: Testing, Safety & Packaging

### AC 7.1: Backend Unit Tests
- [ ] 80%+ code coverage for backend modules
- [ ] Tests for file I/O, JSON parsing, style analysis
- [ ] Tests for error handling and edge cases
- [ ] Run with `pytest`

### AC 7.2: Frontend Unit Tests
- [ ] 80%+ code coverage for React components
- [ ] Tests for UI interactions (upload, approval, generation)
- [ ] Component snapshot tests
- [ ] Run with `vitest` or `jest`

### AC 7.3: Integration Tests
- [ ] End-to-end test: upload document → extract → analyze → approve skill → generate content
- [ ] Test file operations with actual file system
- [ ] Test LiteLLM mocking (don't call real API in tests)
- [ ] Verify outputs match expected structure
- [ ] Verify canonical storage paths for profile, documents, metadata, skills, versions, audit log, and outputs

### AC 7.4: Safety Validation
- [ ] No hardcoded API keys in codebase
- [ ] No SQL database initialization
- [ ] No cloud authentication endpoints
- [ ] No third-party analytics
- [ ] Local file paths use pathlib (cross-platform)
- [ ] Path traversal attempts and malicious filenames are rejected
- [ ] CORS rejects non-development origins during development
- [ ] Logs do not contain API keys, raw document text, or full prompts

### AC 7.5: Documentation
- [ ] README with setup instructions
- [ ] API documentation (Swagger available at `/docs`)
- [ ] Style file format documented
- [ ] Privacy and security assumptions documented
- [ ] Troubleshooting guide

### AC 7.6: Packaging
- [ ] Executable Python requirements.txt or pyproject.toml
- [ ] Frontend build output verified < 500KB gzipped
- [ ] Docker compose file for easier setup (optional)
- [ ] Install script for macOS/Linux/Windows

### AC 7.7: PRD Compliance Check
- [ ] PRD compliance checklist passes all named checks in this document
- [ ] No SQL database added
- [ ] No authentication/login required
- [ ] All data stored locally
- [ ] File structure matches the canonical storage paths listed in TESTING_PLAN.md
- [ ] Rollback creates a new immutable version with `status: "ROLLED_BACK"` and `rolled_back_from_version`
- [ ] Local Only fail-closed routing test passes for analysis, write, and rewrite
- [ ] Evidence snippet filtering test passes for Hybrid and Cloud Allowed

### AC 7.8: Measurable Final Quality Gates
- [ ] Security checklist has zero unresolved Critical or High findings
- [ ] 10K-word analysis completes in < 60s with mocked LLM
- [ ] React rule list renders 100 rules in < 1 second in component test environment
- [ ] Final QA checklist records pass results for local-only mode, extraction, approval, generation, rewrite, audit log, and rollback

---

## Definition of Done

Each sprint is complete when:
1. All acceptance criteria met
2. Code reviewed (no secrets, follows style guide)
3. Tests passing (unit + integration)
4. No regressions in existing features
5. Documentation updated
6. Approved in Phase 4 review
