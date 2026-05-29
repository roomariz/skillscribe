# Detailed Sprint Breakdown

## Overview

7 sprints total, each 1 week (5 business days). No code written; planning only.

---

## Sprint 1: Project Scaffold, FastAPI, React/Vite, Local File Store

**Duration:** Week 1 (May 29 - Jun 2)

**Goal:** Foundation is in place; backend + frontend serve on localhost; file structure initialized.

### Tasks

1. **Project Setup**
   - [ ] Create GitHub repo with .gitignore (data/, .env, node_modules/, *.pyc)
   - [ ] Python project structure: `hermes_writer/` package with `__init__.py`
   - [ ] Node project: `npm init`, install Vite + React + TypeScript
   - [ ] Create `.env.example` with required config keys
   - [ ] Document Python + Node version requirements (Python 3.10+, Node 18+)

2. **FastAPI Backend**
   - [ ] Install FastAPI, Uvicorn, pydantic
   - [ ] Create `main.py` with `/health` endpoint
   - [ ] Setup CORS middleware (allow localhost:5173)
   - [ ] Error handling middleware (catch all errors, return JSON)
   - [ ] Config validation on startup (fail if required env vars missing)
   - [ ] Logging setup (console + file)

3. **React/Vite Frontend**
   - [ ] Create Vite project with React + TypeScript template
   - [ ] Install React Router (for navigation between pages)
   - [ ] Setup axios or fetch client for API calls
   - [ ] Create layout wrapper (header + sidebar + main)
   - [ ] Home page placeholder (ProfileSelector component stub)
   - [ ] Verify build output < 500KB gzipped

4. **Local File Storage**
   - [ ] Create `storage/` module with ProfileStore class
   - [ ] Initialize `./data/profiles/` directory on first run
   - [ ] Implement atomic write function (temp file + rename)
   - [ ] Implement file locking (cross-platform)
   - [ ] Backup function before major writes
   - [ ] Recovery from partial writes

5. **API Scaffolding**
   - [ ] Define request/response schema (Pydantic models)
   - [ ] Stub all endpoints (return empty responses)
   - [ ] Swagger docs available at `/docs`
   - [ ] Version endpoint: `GET /api/version` returns 1.0.0

6. **Testing Setup**
   - [ ] pytest configuration with fixtures
   - [ ] Frontend: vitest + @testing-library/react setup
   - [ ] Coverage thresholds configured (80%)
   - [ ] Pre-commit hooks (optional: linting)

7. **CI/CD Setup**
   - [ ] GitHub Actions workflow on push
   - [ ] Linting job: black, flake8 (backend), eslint (frontend)
   - [ ] Type checking: mypy (backend), tsc (frontend)
   - [ ] Build verification: FastAPI starts, React builds
   - [ ] Test job: pytest + npm test

8. **Documentation**
   - [ ] README: setup instructions (Python env, Node env, run locally)
   - [ ] ARCHITECTURE.md: diagram of backend/frontend/storage split
   - [ ] CONTRIBUTING.md: development workflow
   - [ ] API docs: link to `/docs` Swagger

### Acceptance Criteria
- [ ] Backend serves on localhost:8000
- [ ] Frontend serves on localhost:5173
- [ ] `/health` endpoint returns 200 OK
- [ ] `./data/` directory created on startup
- [ ] CI/CD passes on clean repository
- [ ] Build output < 500KB gzipped

---

## Sprint 2: Profile Management & Document Handling

**Duration:** Week 2 (Jun 3 - Jun 7)

**Goal:** Users can create profiles, upload documents (PDF/DOCX/TXT), see extracted text preview.

### Tasks

1. **Profile Management API**
   - [ ] `POST /api/profiles` → create profile, save to profile.json
   - [ ] `GET /api/profiles` → list all profiles
   - [ ] `GET /api/profiles/{profile_id}` → get profile details
   - [ ] `PUT /api/profiles/{profile_id}` → update display_name, default_skill
   - [ ] `DELETE /api/profiles/{profile_id}` → soft delete
   - [ ] Validate profile_id format (alphanumeric, lowercase)

2. **Profile Storage**
   - [ ] Implement ProfileStore.create_profile()
   - [ ] Implement ProfileStore.get_profile()
   - [ ] Implement ProfileStore.list_profiles()
   - [ ] Implement ProfileStore.update_profile()
   - [ ] Implement ProfileStore.delete_profile() (soft delete)
   - [ ] Ensure atomic writes, file locking

3. **Document Upload API**
   - [ ] `POST /api/profiles/{profile_id}/documents/upload` → multipart file upload
   - [ ] Validate file type (PDF, DOCX, TXT)
   - [ ] Validate file size (max 50MB)
   - [ ] Return 202 with extraction status
   - [ ] Implement background extraction task (sync for Phase 1)

4. **Document Extraction**
   - [ ] Implement pdf extraction (PyMuPDF library)
   - [ ] Implement docx extraction (python-docx library)
   - [ ] Implement txt extraction (read as-is)
   - [ ] Save extracted text to `documents/extracted/{doc_id}.txt`
   - [ ] Save metadata to `data/profiles/{profile_id}/documents/metadata/{doc_id}.json`
   - [ ] Handle extraction errors gracefully
   - [ ] Support manual text upload as fallback

5. **Document List & Preview**
   - [ ] `GET /api/profiles/{profile_id}/documents` → list documents
   - [ ] `GET /api/profiles/{profile_id}/documents/{doc_id}` → get document + text
   - [ ] `PUT /api/profiles/{profile_id}/documents/{doc_id}` → update extracted text (manual edit)
   - [ ] `DELETE /api/profiles/{profile_id}/documents/{doc_id}` → delete document

6. **Frontend: Profile Selector**
   - [ ] Component shows list of profiles
   - [ ] Create new profile form (profile_id, display_name)
   - [ ] Validation: profile_id required, unique
   - [ ] Select profile → redirect to Dashboard

7. **Frontend: Profile Dashboard**
   - [ ] Show profile name, metadata (skill count, document count)
   - [ ] Documents panel: list documents, preview button
   - [ ] Upload button: open file picker
   - [ ] Progress indicator during extraction

8. **Frontend: Document Upload & Preview**
   - [ ] Drag-and-drop file upload
   - [ ] File picker button
   - [ ] Upload progress bar
   - [ ] Show extracted text in editor (read-only by default)
   - [ ] Option to edit text manually
   - [ ] [Done] → save document, return to Dashboard

9. **Testing**
   - [ ] Backend: upload document, verify file saved to correct path
   - [ ] Backend: extract PDF/DOCX/TXT, verify text content
   - [ ] Backend: invalid file type rejected
   - [ ] Backend: file size limit enforced
   - [ ] Frontend: upload document, see preview
   - [ ] Frontend: manual text edit persists

### Acceptance Criteria
- [ ] User can create profile
- [ ] User can upload PDF/DOCX/TXT
- [ ] User sees extraction progress
- [ ] User sees extracted text preview
- [ ] User can edit extracted text
- [ ] Files stored at correct paths
- [ ] Tests passing (80%+ coverage)

---

## Sprint 3: Privacy Routing, Style Analysis & Rule Extraction

**Duration:** Week 3 (Jun 8 - Jun 12)

**Goal:** Privacy routing is enforced before any LLM analysis; system analyzes uploaded documents, extracts style rules, shows rules to user with evidence.

### Tasks

1. **Privacy & Provider Routing Foundation**
   - [ ] Implement privacy modes before any style analysis call: Local Only, Hybrid, Cloud Allowed
   - [ ] Local Only uses Ollama only and fails closed if Ollama is unavailable
   - [ ] Hybrid uses Ollama first and may use controlled hosted fallback only after user selection
   - [ ] Cloud Allowed permits selected cloud providers through LiteLLM
   - [ ] Enforce all provider calls through LiteLLM only
   - [ ] Add routing matrix tests for each privacy mode

2. **LiteLLM Integration**
   - [ ] Install LiteLLM client dependency or configure OpenAI-compatible calls to LiteLLM proxy
   - [ ] Implement LiteLLMClient wrapper for completion calls through LiteLLM only
   - [ ] Configure LiteLLM with Ollama, OpenRouter, Gemini, Groq, Mistral, OpenAI as selected providers
   - [ ] Test Ollama connectivity (localhost:11434)
   - [ ] Implement retry logic (exponential backoff, 3 attempts max)
   - [ ] Timeout handling (abort after 60s)

3. **Style Analyzer Module**
   - [ ] Implement `StyleAnalyzer.analyze_documents(doc_ids)` → returns list of rules
   - [ ] Load extracted text from documents
   - [ ] Call LLM (via LiteLLM) to identify writing patterns only after privacy routing is enforced
   - [ ] Extract rules with categories: tone, structure, vocabulary, formality, other
   - [ ] Map each rule back to source snippets from documents
   - [ ] Calculate confidence score (0-1) for each rule

4. **Prompt Engineering**
   - [ ] System prompt explaining task: identify style patterns
   - [ ] In Local Only, extracted text may be embedded in the prompt sent to local Ollama
   - [ ] In Hybrid or Cloud Allowed, raw document snippets must not be sent to hosted providers; use approved style rules, abstractions, and summaries only
   - [ ] Request JSON response with structure:
     ```json
     {"rules": [{"category": "...", "description": "...", "examples": {...}, "confidence": 0.9}]}
     ```
   - [ ] Test with sample documents, iterate on prompt

5. **Rule Approval UI**
   - [ ] Analyze endpoint: `POST /api/profiles/{profile_id}/analyze-style`
   - [ ] Request: document_ids, skill_name
   - [ ] Response: 202 with analysis_id
   - [ ] `GET /api/profiles/{profile_id}/analyze-style/{analysis_id}` → returns rules

6. **Frontend: Rule Review Page**
   - [ ] Show analysis progress during LLM call
   - [ ] Display all rules as cards
   - [ ] Each rule shows: category, description, examples, evidence snippets, confidence %
   - [ ] Checkboxes: Approve, Reject for each rule
   - [ ] [Edit] button to tweak rule (modal)
   - [ ] [Add Custom Rule] button (modal to add manual rule)
   - [ ] [Approve All] shortcut
   - [ ] [Next] button → go to Skill Approval

7. **Edit Rule Modal**
   - [ ] Edit description, examples, confidence threshold
   - [ ] Save changes (modify in-memory, not persisted yet)
   - [ ] Cancel (discard changes)

8. **Custom Rule Modal**
   - [ ] Form: category dropdown, description, examples, confidence
   - [ ] Add rule to list with `source: "user_authored"` and `evidence: null`
   - [ ] Remove custom rule if desired

9. **Processing Status Feedback**
   - [ ] Show spinner during analysis
   - [ ] Update progress percentage
   - [ ] Estimated time remaining
   - [ ] [Cancel] button (stops analysis, discards results)

10. **Testing**
   - [ ] Backend: analyze documents, receive rules
   - [ ] Backend: rules include evidence snippets
   - [ ] Backend: confidence scores generated
   - [ ] Backend: Local Only fails closed if Ollama unavailable
   - [ ] Backend: hosted provider prompts exclude raw document snippets
   - [ ] Frontend: rule cards display correctly
   - [ ] Frontend: approve/reject state persists
   - [ ] Frontend: custom rule addition works

### Acceptance Criteria
- [ ] LLM analysis completes successfully
- [ ] Rules include evidence snippets from documents
- [ ] User sees all rules with approve/reject options
- [ ] User can edit rules and add custom rules
- [ ] Analysis can be cancelled mid-process
- [ ] Local Only never calls a cloud provider
- [ ] Tests passing (80%+ coverage)

---

## Sprint 4: Skill Review, Approval & Versioning

**Duration:** Week 4 (Jun 13 - Jun 17)

**Goal:** User approves rules, skill is created and versioned, audit log tracks all changes.

### Tasks

1. **Skill Approval Endpoint**
   - [ ] `POST /api/profiles/{profile_id}/analyze-style/{analysis_id}/approve`
   - [ ] Request: approved_rules, rejected_rules, custom_rules
   - [ ] Create skill.json with approved rules
   - [ ] Save to `skills/{skill_id}/skill.json`
   - [ ] Set status to "PENDING"
   - [ ] Return skill object

2. **Skill Creation Storage**
   - [ ] Implement SkillStore.create_skill()
   - [ ] Implement SkillStore.get_skill()
   - [ ] Implement SkillStore.list_skills()
   - [ ] Implement SkillStore.approve_skill()
   - [ ] Implement SkillStore.mark_superseded()
   - [ ] Implement SkillStore.delete_skill() (soft delete)

3. **Skill Approval UI**
   - [ ] Show skill confirmation details
   - [ ] Display file path where skill is stored
   - [ ] Show counts: approved rules, rejected rules, custom rules
   - [ ] [View Full Skill JSON] → expand JSON viewer
   - [ ] [Create Skill] → save skill, show confirmation
   - [ ] [Cancel] → discard, return to Dashboard
   - [ ] [Back] → return to rule review

4. **Versioning System**
   - [ ] Implement SkillVersioner class
   - [ ] On skill update, increment version number
   - [ ] Save each version as `v{N}.skill.json`
   - [ ] Keep current version as `skill.json` (symlink or copy)
   - [ ] Maintain `metadata.json` with version history

5. **Version History UI**
   - [ ] `GET /api/profiles/{profile_id}/skills/{skill_id}/versions` → list versions
   - [ ] Show version number, date, status, rule count
   - [ ] [View] → show version contents
   - [ ] [Rollback] → revert to this version

6. **Rollback Implementation**
   - [ ] `POST /api/profiles/{profile_id}/skills/{skill_id}/rollback`
   - [ ] Request: target_version, reason
   - [ ] Verify version file exists
   - [ ] Copy selected version forward into a new immutable version
   - [ ] Set new version status to "ROLLED_BACK"
   - [ ] Record `rolled_back_from_version`
   - [ ] Copy new version to active skill.json
   - [ ] Log rollback event in `data/profiles/{profile_id}/skills/{skill_id}/audit/audit.jsonl`

7. **Audit Logging**
   - [ ] Implement AuditLogger class (append-only JSONL)
   - [ ] Create `data/profiles/{profile_id}/skills/{skill_id}/audit/audit.jsonl` for each skill
   - [ ] Log events: skill_created, rule_approved, rule_rejected, skill_approved, skill_rollback, skill_deleted
   - [ ] Each log entry: timestamp, event_type, actor, details
   - [ ] Verify immutability (no edits after write)

8. **Audit Log UI**
   - [ ] `GET /api/profiles/{profile_id}/skills/{skill_id}/audit`
   - [ ] Show audit log entries in timeline view
   - [ ] Display event type, actor, timestamp, details

9. **Frontend: Skill List**
   - [ ] Dashboard shows all skills
   - [ ] Each skill card: name, version, status, rule count
   - [ ] [Use] → redirect to Write/Rewrite page
   - [ ] [Edit] → (future: iterate on skill)
   - [ ] [View Versions] → show version history
   - [ ] [Delete] → soft delete skill
   - [ ] Set as default skill (context menu or star button)

10. **Testing**
    - [ ] Backend: skill creation, verify file saved
    - [ ] Backend: skill versioning, verify versions saved
    - [ ] Backend: rollback, verify previous version restored
    - [ ] Backend: audit log immutable after write
    - [ ] Frontend: approve skill, see in skill list
    - [ ] Frontend: rollback skill, version incremented
    - [ ] Frontend: audit log displays correctly

### Acceptance Criteria
- [ ] Skill created and saved to correct path
- [ ] Skill versioning works (v1, v2, etc.)
- [ ] Rollback restores previous version correctly
- [ ] Audit log tracks all changes
- [ ] User sees skill list with versions
- [ ] Tests passing (80%+ coverage)

---

## Sprint 5: Provider Configuration & Privacy Settings

**Duration:** Week 5 (Jun 18 - Jun 22)

**Goal:** Users can configure selected LLM providers and choose the already-enforced privacy mode.

### Tasks

1. **Provider Detection**
   - [ ] On startup, detect available providers
   - [ ] Ping Ollama at localhost:11434
   - [ ] Check for cloud provider API keys in .env
   - [ ] Log available providers to config

2. **Privacy Modes**
   - [ ] Mode 1: Local Only (Ollama only; fail closed)
   - [ ] Mode 2: Hybrid (Ollama first; controlled hosted fallback after user selection)
   - [ ] Mode 3: Cloud Allowed (selected cloud providers permitted)
   - [ ] Store mode in profile.json or config
   - [ ] Respect mode during all LLM calls

3. **Content Redaction**
   - [ ] Implement Redactor class
   - [ ] Before sending to cloud provider, remove raw document snippets
   - [ ] Send only approved style rules, abstractions, summaries, and user prompts; not raw document text
   - [ ] For local Ollama, no redaction needed (data stays local)
   - [ ] Verify redaction in tests

4. **Settings Page Backend**
   - [ ] `GET /api/config` → current config (providers, privacy mode)
   - [ ] `POST /api/config/update-privacy-mode` → change privacy mode
   - [ ] `POST /api/config/test-provider` → test connection to provider
   - [ ] Document provider keys as `.env` configuration; do not add a credential-write API

5. **Settings Page Frontend**
   - [ ] Show available providers with status (connected, available)
   - [ ] Display model names
   - [ ] Privacy mode selector: radio buttons or dropdown
   - [ ] Show cloud provider key status from `.env`; do not write credentials through the UI
   - [ ] [Test Connection] for each provider
   - [ ] Show test results (success or error message)
   - [ ] Save settings

6. **Error Handling**
   - [ ] If primary provider unavailable, apply privacy-mode routing rules
   - [ ] Log provider used for each operation
   - [ ] Show user-friendly error in Local Only: "Ollama not found. Local Only mode prevents cloud fallback."
   - [ ] If all providers fail, show setup instructions

7. **LiteLLM Configuration**
   - [ ] Ensure LiteLLM router is configured with all available providers
   - [ ] Respect privacy mode when routing
   - [ ] Implement fallback chain only for Hybrid and Cloud Allowed modes
   - [ ] Retry logic with exponential backoff

8. **Testing**
   - [ ] Backend: Ollama detection works
   - [ ] Backend: provider fallback works only when mode permits it
   - [ ] Backend: redaction preserves style intent
   - [ ] Backend: privacy mode enforced (no cloud calls in Local Only mode)
   - [ ] Frontend: settings page loads and saves correctly
   - [ ] Frontend: connection test shows proper feedback

### Acceptance Criteria
- [ ] Ollama detected on startup
- [ ] Privacy modes selectable by user
- [ ] Provider fallback works only in Hybrid or Cloud Allowed
- [ ] User content redacted before cloud provider call
- [ ] Settings page functional
- [ ] Tests passing (80%+ coverage)

---

## Sprint 6: Write & Rewrite Workflows

**Duration:** Week 6 (Jun 23 - Jun 27)

**Goal:** Users can generate new writing using approved skills, or rewrite existing text.

### Tasks

1. **Write Workflow API**
   - [ ] `POST /api/profiles/{profile_id}/write` → generate new content
   - [ ] Request: skill_id, prompt, context (optional), temperature, max_tokens
   - [ ] Load skill from skill.json
   - [ ] Embed skill rules in LLM prompt
   - [ ] Call LLM
   - [ ] Save output under `data/profiles/{profile_id}/skills/{skill_id}/outputs/` as `draft-{id}.md`
   - [ ] Return generation_id with status

2. **Rewrite Workflow API**
   - [ ] `POST /api/profiles/{profile_id}/rewrite` → rewrite existing text
   - [ ] Request: skill_id, original_text, instructions (optional), temperature
   - [ ] Load skill from skill.json
   - [ ] Call LLM with style rules + original text
   - [ ] Save output under `data/profiles/{profile_id}/skills/{skill_id}/outputs/` as `rewrite-{id}.md`
   - [ ] Store original + rewritten for comparison

3. **Prompt Engineering**
   - [ ] System prompt: "Rewrite the following using this style: [rules as bullets]"
   - [ ] Include evidence snippets only for Local Only prompts; hosted provider prompts use abstractions and summaries
   - [ ] Temperature guidance: 0.5 for consistency, 0.7 for creativity
   - [ ] Max tokens limit (default 500 for write, 300 for rewrite)

4. **Output Storage**
   - [ ] Implement OutputStore class
   - [ ] Save outputs with metadata: skill_id, version, model, timestamp
   - [ ] Output format: Markdown with YAML frontmatter
   - [ ] Include prompt and model name in frontmatter

5. **Frontend: Write/Rewrite Page**
   - [ ] Tabs: Write, Rewrite
   - [ ] Skill selector dropdown
   - [ ] Prompt/text input field with character counter
   - [ ] Context field (optional)
   - [ ] Advanced options: temperature slider, max_tokens input
   - [ ] [Generate]/[Rewrite] button
   - [ ] Output display area

6. **Output Display & Actions**
   - [ ] Show generated content in editor
   - [ ] [Copy] → copy to clipboard
   - [ ] [Save] → save output to profile
   - [ ] [Export] → download as .md or .txt
   - [ ] [Discard] → clear output without saving

7. **Rewrite-Specific Features**
   - [ ] [Side-by-Side Diff] → show original vs rewritten
   - [ ] Diff highlighting: changed words/phrases highlighted
   - [ ] [Copy Original] / [Copy Rewritten]

8. **Generation Status**
   - [ ] Show progress spinner during generation
   - [ ] Show elapsed time and model name
   - [ ] [Cancel] button (stops generation, discards result)

9. **Output History**
   - [ ] Dashboard shows recent outputs (3-5)
   - [ ] `GET /api/profiles/{profile_id}/outputs` → list all outputs
   - [ ] Each output: type, skill, date, preview
   - [ ] [View Full], [Copy], [Delete] actions

10. **Testing**
    - [ ] Backend: generate content with valid skill
    - [ ] Backend: rewrite content with valid skill
    - [ ] Backend: output saved to correct path
    - [ ] Backend: output metadata includes model, timestamp
    - [ ] Frontend: write tab loads, prompt input works
    - [ ] Frontend: rewrite tab loads, original text input works
    - [ ] Frontend: output displays correctly
    - [ ] Frontend: side-by-side diff shows difference

### Acceptance Criteria
- [ ] User can generate new writing using skill
- [ ] User can rewrite existing text using skill
- [ ] Output saved with metadata
- [ ] Output history accessible
- [ ] Output can be copied, exported, or discarded
- [ ] Tests passing (80%+ coverage)

---

## Sprint 7: Testing, Safety Hardening & Packaging

**Duration:** Week 7 (Jun 28 - Jul 2)

**Goal:** MVP complete, tested, safe, packaged for release.

### Tasks

1. **Backend Unit Tests**
   - [ ] File I/O tests (80%+ coverage)
   - [ ] Document extraction tests (80%+ coverage)
   - [ ] Style analysis tests (80%+ coverage)
   - [ ] API request/response tests (80%+ coverage)
   - [ ] Versioning & audit log tests (80%+ coverage)
   - [ ] LiteLLM integration tests with mocks (80%+ coverage)
   - [ ] Privacy & redaction tests (80%+ coverage)
   - [ ] Run `pytest --cov=hermes_writer --cov-fail-under=80`

2. **Frontend Unit Tests**
   - [ ] Component tests: ProfileSelector, DocumentUpload, RuleReview, SkillApproval, WriteRewrite (80%+ coverage)
   - [ ] Hook tests: useProfile, useDocuments, useSkills (80%+ coverage)
   - [ ] Run `npm test -- --coverage --coverageReporters=html`

3. **Integration Tests**
   - [ ] Backend: upload → extract → analyze → skill creation workflow
   - [ ] Backend: write/rewrite workflow
   - [ ] Frontend: profile creation → upload → analysis → skill approval
   - [ ] Backend + Frontend: E2E flow (optional Playwright)

4. **Safety Validation**
   - [ ] No hardcoded API keys in codebase
   - [ ] No SQL database initialization
   - [ ] No cloud authentication endpoints
   - [ ] No third-party analytics
   - [ ] Cross-platform path handling (pathlib)
   - [ ] User data never leaked in logs
   - [ ] Error messages don't expose sensitive data

5. **Performance Testing**
   - [ ] Frontend: rule list render (100 rules) smooth
   - [ ] Frontend: text preview scroll (1M characters) smooth
   - [ ] Backend: analyze document (10K words) completes in < 60s
   - [ ] Build output: React bundle < 500KB gzipped

6. **Security Review**
   - [ ] OWASP Top 10 check (no XSS, SQLi, CSRF, etc.)
   - [ ] CORS properly configured
   - [ ] Error responses don't leak stack traces
   - [ ] File paths sanitized
   - [ ] User input validated at all boundaries

7. **Documentation**
   - [ ] README: complete setup + usage instructions
   - [ ] API docs: Swagger available at `/docs`
   - [ ] Architecture: system design explained
   - [ ] Contributing: dev workflow guide
   - [ ] Storage model: file structure explained
   - [ ] Troubleshooting: common issues + solutions
   - [ ] Privacy: what data is stored, where

8. **Packaging**
   - [ ] Python requirements: requirements.txt or pyproject.toml
   - [ ] Frontend build: `npm run build` produces dist/
   - [ ] Docker compose (optional): one-command local setup
   - [ ] Installation script: setup.sh or setup.ps1 (cross-platform)
   - [ ] Version: set to 1.0.0 in package.json, pyproject.toml

9. **PRD Compliance Check**
   - [ ] ✓ All 7 sprints completed
   - [ ] ✓ No SQL database added
   - [ ] ✓ No authentication/login required
   - [ ] ✓ All data stored locally in files
   - [ ] ✓ File structure matches design
   - [ ] ✓ Versioning & rollback working
   - [ ] ✓ Audit log tracking changes
   - [ ] ✓ LiteLLM integration working
   - [ ] ✓ Privacy modes enforced
   - [ ] ✓ Tests passing (80%+ coverage)
   - [ ] ✓ Documentation complete

10. **Final QA**
    - [ ] Test on macOS, Linux, Windows
    - [ ] Test with Ollama local, Hybrid controlled fallback, and Cloud Allowed routing
    - [ ] Test profile creation, document upload, skill approval, write/rewrite
    - [ ] Test skill rollback, audit log
    - [ ] Test privacy modes
    - [ ] Performance acceptable
    - [ ] No console errors or warnings

11. **Release Preparation**
    - [ ] Bump version to 1.0.0
    - [ ] Update CHANGELOG
    - [ ] Tag release in git: `git tag v1.0.0`
    - [ ] Create GitHub release with notes
    - [ ] Verify build passes CI/CD
    - [ ] Announce release (optional)

### Acceptance Criteria
- [ ] All unit tests passing (80%+ coverage)
- [ ] All integration tests passing
- [ ] Security checklist has zero unresolved Critical or High findings
- [ ] Performance thresholds pass: 10K-word analysis completes in < 60s with mocked LLM; React bundle remains < 500KB gzipped
- [ ] Documentation complete
- [ ] Packaging ready (requirements.txt, build scripts)
- [ ] PRD compliance checklist passes all named checks
- [ ] Final QA checklist has all required local-only, extraction, approval, generation, rewrite, audit, and rollback checks marked pass
- [ ] Release tagged and announced

---

## Cross-Sprint Concerns

### Testing Throughout
- Every sprint adds unit tests for new code
- Integration tests for workflows
- Maintain 80%+ coverage
- Code review includes test review

### Documentation Throughout
- Update API docs as endpoints added
- Add architecture notes each sprint
- Troubleshooting section grows as issues found
- Changelog updated

### CI/CD Throughout
- All checks must pass before merge
- Linting, type checking, tests, build verification
- Coverage report generated
- Blocked on coverage regression

### Security Throughout
- No credentials in code or .env defaults
- Input validation at all boundaries
- Errors logged safely (no PII in logs)
- Review OWASP issues each sprint

### Performance Throughout
- Build size monitored
- Runtime performance measured
- No N+1 queries (file operations)
- Caching where appropriate

### User Data Safety Throughout
- All writes atomic (temp file + rename)
- Backups before major modifications
- Audit log for all changes
- Recovery procedures documented
