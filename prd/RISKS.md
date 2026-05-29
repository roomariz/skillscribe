# Risk Analysis

## High-Risk Areas

### 1. Document Extraction Accuracy
**Risk:** PDF/DOCX extraction may fail or corrupt text, especially with complex formatting or non-English text.
**Probability:** High | **Impact:** High
**Mitigation:**
- Use proven libraries (PyMuPDF, python-docx)
- Implement fallback extraction methods
- Store original documents for manual review
- Preview extracted text before style analysis
- Support manual text upload as fallback

### 2. Style Analysis Reliability
**Risk:** LLM-based style extraction may produce inconsistent or inaccurate rules from user documents.
**Probability:** High | **Impact:** High
**Mitigation:**
- Show evidence snippets for each rule (trace to source)
- Allow user to approve/reject/edit each rule
- Let users add custom rules manually
- Version all skill outputs (enable rollback)
- Test with diverse user samples

### 3. Local LLM Availability
**Risk:** User's local Ollama instance may not be running or may have insufficient resources.
**Probability:** Medium | **Impact:** High
**Mitigation:**
- Detect Ollama availability on startup
- Provide clear error messages with setup instructions
- Support controlled hosted fallback only in Hybrid or Cloud Allowed modes
- In Local Only, fail closed if Ollama is unavailable
- Cache model responses where possible
- Document system requirements

### 4. File Permissions & Corruption
**Risk:** Local file system issues (permission denied, disk full, encoding issues) could corrupt user data.
**Probability:** Low | **Impact:** Critical
**Mitigation:**
- Write to temporary file, then atomic rename
- Store backups before major operations
- Validate JSON before write (schema validation)
- Recover from partial writes
- Regular data integrity checks

### 5. Privacy Leakage via LiteLLM Logs
**Risk:** LiteLLM or provider may log sensitive user document content.
**Probability:** Medium | **Impact:** High
**Mitigation:**
- Only send raw document text to local Ollama in Local Only mode
- For hosted providers, send approved style rules, abstractions, and summaries; never raw snippets
- Filter evidence snippets before hosted LLM calls
- Document privacy implications in UI
- Support Local Only mode with fail-closed Ollama routing
- Audit what is sent to each provider

### 6. Skill Namespace Collision
**Risk:** Multiple users (future: local profile switching) may create skills with same name.
**Probability:** Low | **Impact:** Medium
**Mitigation:**
- Namespace skills by profile_id + skill_name
- Enforce unique skill IDs
- Warn on skill creation if similar skill exists

### 7. LiteLLM Provider Routing Failures
**Risk:** LiteLLM misconfiguration or provider API changes break model access.
**Probability:** Low | **Impact:** High
**Mitigation:**
- Validate provider config on startup
- Implement retry logic with exponential backoff
- Support manual provider fallback only when Hybrid or Cloud Allowed permits it
- Log all LiteLLM calls for debugging
- Version LiteLLM config separately

### 8. UI State Sync with Backend
**Risk:** Frontend state may diverge from backend file state if operations fail mid-process.
**Probability:** Medium | **Impact:** Medium
**Mitigation:**
- All operations are idempotent where possible
- Store operation intent log in files
- Implement recovery from crash mid-operation
- Validate UI state against file state on load
- Queue operations with undo/redo

### 9. Scale to Multiple Profiles
**Risk:** File-based storage may struggle if users create thousands of profiles/skills/documents.
**Probability:** Very Low (Phase 1) | **Impact:** Medium
**Mitigation:**
- Design file structure to support future SQL migration
- Document directory size limits
- Add warnings when profile reaches 10k files
- Plan Phase 2 migration path

### 10. Rollback Version Integrity
**Risk:** Skill rollback may fail if the selected immutable version file is missing or structurally invalid.
**Probability:** Low | **Impact:** High
**Mitigation:**
- Store complete immutable skill version files, not just diffs
- Audit logs record rollback events only and are not used to restore files
- Rollback copies a selected immutable version into a new immutable version
- New rollback version records `status = ROLLED_BACK`, `rolled_back_from_version`, `rollback_reason`, and rollback timestamp
- Implement rollback validation before commit
- Test copy-forward rollback paths in CI/CD

## Medium-Risk Areas

### 11. Model Version Compatibility
**Risk:** Retraining or updating Ollama models changes skill generation behavior.
**Probability:** Medium | **Impact:** Medium
**Mitigation:**
- Lock model versions in LiteLLM config
- Document model constraints in skill files
- Show model version in skill metadata

### 12. Concurrent File Operations
**Risk:** Two operations writing to same file simultaneously corrupts data.
**Probability:** Low (single-user initially) | **Impact:** Critical
**Mitigation:**
- Use file locking (fcntl on Linux, msvcrt on Windows)
- Single-threaded backend operations initially
- Document thread safety assumptions

### 13. UI Performance with Large Documents
**Risk:** Uploading 50MB PDFs or extracting 1M word documents hangs UI.
**Probability:** Medium | **Impact:** Medium
**Mitigation:**
- Streaming upload progress
- Chunked processing with background workers
- Limits on document size
- Clear feedback on processing status

## Low-Risk Areas

### 14. Cross-Platform File Paths
**Risk:** Windows/Mac/Linux path handling inconsistencies.
**Probability:** Low | **Impact:** Low
**Mitigation:**
- Use pathlib (Python) / Path.join (consistent cross-platform)
- Test on Windows, Mac, Linux in CI/CD

### 15. Browser Security (CORS, CSP)
**Risk:** Frontend XSS or CSRF due to improper React/API setup.
**Probability:** Low (local-only) | **Impact:** Medium
**Mitigation:**
- Follow React security best practices
- Validate all API inputs on backend
- Implement CSP headers
- No third-party iframes

## Risk Response Strategy

| Risk | Response | Owner | Timeline |
|------|----------|-------|----------|
| Document extraction | Implement fallback + preview | Sprint 2 | Week 2 |
| Style analysis reliability | User approval UX + versioning | Sprint 3-4 | Week 3-4 |
| Local LLM availability | Detect Ollama + fail closed in Local Only | Sprint 3-5 | Week 3-5 |
| File corruption | Atomic writes + backup | Sprint 1 | Week 1 |
| Privacy leakage | Privacy routing before analysis + evidence filtering | Sprint 3-5 | Week 3-5 |
| Concurrent writes | File locking | Sprint 1 | Week 1 |
| Performance | Streaming + workers | Sprint 3-6 | Week 3+ |
