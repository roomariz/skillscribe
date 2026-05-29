# Acceptance Criteria

## Sprint 1: Project Scaffold & Local Storage

### AC 1.1: FastAPI Backend Runs Locally
- [ ] FastAPI server starts without errors on `localhost:8000`
- [ ] Health check endpoint `GET /health` returns `{"status": "ok"}`
- [ ] Serves React frontend on `GET /` (proxied or served)
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
- [ ] Startup fails with clear error if required config missing
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
- [ ] PDF extraction produces readable text (using pypdf or similar)
- [ ] DOCX extraction preserves text structure (python-docx)
- [ ] TXT files parsed as-is
- [ ] Extracted text stored at `data/profiles/{profile_id}/documents/extracted/{doc_id}.txt`
- [ ] Extraction failures logged; user shown error message
- [ ] Fallback: user can paste extracted text manually

### AC 2.4: Text Preview
- [ ] UI shows extracted text in read-only editor
- [ ] Preview is live-scrollable and searchable (Ctrl+F)
- [ ] Character count displayed
- [ ] Option to edit extracted text manually before analysis
- [ ] Changes saved if user approves

### AC 2.5: Metadata Storage
- [ ] Document metadata file: `data/profiles/{profile_id}/documents/{doc_id}/meta.json`
- [ ] Includes: original filename, upload date, extraction date, word count, character count
- [ ] Audit log entry for each upload

---

## Sprint 3: Style Analysis & Rule Extraction

### AC 3.1: Style Analyzer Initialization
- [ ] Backend loads extracted text documents
- [ ] Identifies writing patterns (sentence structure, vocabulary, tone, formality)
- [ ] Uses LLM (via LiteLLM) to generate style rules
- [ ] Calls trace each rule back to source document snippet

### AC 3.2: Rule Generation
- [ ] LLM produces JSON rules with structure:
  - `rule_id`, `category` (tone, structure, vocabulary, etc.)
  - `description`, `examples` (positive + negative)
  - `source_snippets` (list of document excerpts that support rule)
- [ ] At least 10-20 rules per profile
- [ ] Rules are actionable (can be checked programmatically or by LLM)

### AC 3.3: Rule Preview & Approval
- [ ] UI shows each rule with evidence snippets
- [ ] User can approve, reject, or edit each rule
- [ ] Rejected rules not included in skill
- [ ] Edited rules stored with user modification note
- [ ] Ability to add custom rules manually

### AC 3.4: Proposed Skill File
- [ ] System generates `skill.json` with approved rules
- [ ] Stored at `data/profiles/{profile_id}/skills/{skill_id}/skill.json`
- [ ] Includes: skill_id, profile_id, name, version, created_at, rules array
- [ ] Skill is read-only until approved

### AC 3.5: Processing Status
- [ ] User sees progress indication during style analysis
- [ ] Estimated time shown if analysis is long
- [ ] Option to cancel analysis (safe rollback)
- [ ] Logs all processing steps in audit file

---

## Sprint 4: Skill Review, Approval & Versioning

### AC 4.1: Skill Approval Workflow
- [ ] User reviews proposed skill JSON
- [ ] Option to approve, reject, or iterate
- [ ] Approved skills moved to `active` state
- [ ] Status stored in skill.json: `"status": "approved"`
- [ ] Approval timestamp and approver recorded

### AC 4.2: Active Skill Registry
- [ ] UI lists all active skills for profile
- [ ] Default skill selectable and persisted in profile.json
- [ ] Inactive skills archived but recoverable

### AC 4.3: Versioning
- [ ] Each skill change creates new version: `v1.skill.json`, `v2.skill.json`
- [ ] Version history visible in UI
- [ ] Version metadata includes: date, change summary, diff from previous

### AC 4.4: Rollback
- [ ] User can rollback to any previous skill version
- [ ] Rollback is logged in audit log
- [ ] Current skill version always points to latest approved
- [ ] Restored version is copied (not reverted in-place)

### AC 4.5: Audit Logging
- [ ] `data/profiles/{profile_id}/skills/{skill_id}/audit.jsonl` created
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
- [ ] Fallback to cloud provider if Ollama unavailable
- [ ] User configurable via .env: `OLLAMA_BASE_URL`

### AC 5.3: Privacy Modes
- [ ] Mode 1: Ollama-only (no cloud calls)
- [ ] Mode 2: Ollama + Fallback (tries cloud if local fails)
- [ ] Mode 3: Cloud-only (explicit opt-in)
- [ ] User selects mode in UI; persisted in profile
- [ ] Redact user document content before sending to cloud providers

### AC 5.4: Provider Configuration UI
- [ ] Settings page shows available providers
- [ ] User can add API keys for cloud providers (Groq, Mistral, OpenAI, etc.)
- [ ] Test connection button validates each provider
- [ ] Configuration stored in `.env` (not in user files)

### AC 5.5: Provider Fallback
- [ ] If primary provider fails, attempt fallback
- [ ] Retry logic with exponential backoff (3 attempts max)
- [ ] User informed of provider switch
- [ ] Log provider used for each operation

### AC 5.6: Error Handling
- [ ] Clear error messages for provider failures
- [ ] Fallback to local Ollama if cloud provider unavailable
- [ ] Suggest setup steps if no provider available

---

## Sprint 6: Write & Rewrite Workflows

### AC 6.1: Write Workflow
- [ ] User opens "New Document" modal
- [ ] Selects active skill from dropdown
- [ ] Optionally provides writing prompt or outline
- [ ] Clicks "Generate" to create new writing using skill
- [ ] Backend sends prompt + approved skill rules to LLM
- [ ] Generated text displayed in editor

### AC 6.2: Write Output Storage
- [ ] Generated document saved to `data/profiles/{profile_id}/skills/{skill_id}/outputs/draft-{id}.md`
- [ ] Metadata includes: skill version used, LLM model, generation date, prompt
- [ ] User can save, edit, or discard output

### AC 6.3: Rewrite Workflow
- [ ] User uploads or pastes existing text
- [ ] Selects active skill
- [ ] Clicks "Rewrite" to apply skill style to text
- [ ] Backend sends text + skill rules to LLM
- [ ] Rewritten text displayed with diff view

### AC 6.4: Rewrite Output Storage
- [ ] Rewritten document saved to `data/profiles/{profile_id}/skills/{skill_id}/outputs/rewrite-{id}.md`
- [ ] Original text included in metadata for reference
- [ ] Diff preserved (original + rewritten)

### AC 6.5: LLM Prompt Engineering
- [ ] System prompt explains skill context
- [ ] Skill rules embedded in prompt as bullet points
- [ ] Evidence snippets included for context
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

### AC 7.4: Safety Validation
- [ ] No hardcoded API keys in codebase
- [ ] No SQL database initialization
- [ ] No cloud authentication endpoints
- [ ] No third-party analytics
- [ ] Local file paths use pathlib (cross-platform)

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
- [ ] Verify all features match initial PRD
- [ ] No SQL database added
- [ ] No authentication/login required
- [ ] All data stored locally
- [ ] File structure matches design
- [ ] Versioning and rollback working

---

## Definition of Done

Each sprint is complete when:
1. All acceptance criteria met
2. Code reviewed (no secrets, follows style guide)
3. Tests passing (unit + integration)
4. No regressions in existing features
5. Documentation updated
6. Approved in Phase 4 review
