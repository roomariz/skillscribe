# Testing Plan

## Test Strategy

**Target Coverage:** 80%+

**Test Types:** Unit, Integration, E2E

**Tools:**
- **Backend:** pytest (Python), fixtures for file I/O
- **Frontend:** vitest or jest (JavaScript/TypeScript)
- **E2E:** Playwright (optional, for critical paths)
- **Coverage:** pytest-cov, nyc/c8

---

## Unit Tests

### Backend (Python / FastAPI)

#### 1. File I/O & Storage Tests
```python
test_create_profile_directory_structure()
test_write_profile_json_atomically()
test_read_profile_json_valid_data()
test_read_profile_json_corrupted_file()
test_update_profile_json_preserves_other_fields()
test_delete_profile_soft_delete()
test_file_locking_prevents_concurrent_writes()
test_rollback_rejects_corrupted_version_file()
test_storage_path_contract_profile()
test_storage_path_contract_documents()
test_storage_path_contract_skill_versions()
test_storage_path_contract_audit_log()
test_storage_path_contract_outputs()
```

**Module:** `hermes_writer/storage/profile_store.py`

#### 2. Document Extraction Tests
```python
test_extract_pdf_valid_file()
test_extract_pdf_invalid_file()
test_extract_docx_valid_file()
test_extract_txt_valid_file()
test_extract_preserves_line_breaks()
test_extract_handles_unicode_characters()
test_extract_handles_empty_document()
test_extract_returns_metadata(filename, word_count, char_count)
test_extract_pdf_metadata_method_is_pymupdf()
test_extraction_timeout_after_30_seconds()
```

**Module:** `hermes_writer/extraction/document_extractor.py`

#### 3. Style Analysis Tests
```python
test_analyze_style_extracts_rules()
test_analyze_style_includes_evidence_snippets()
test_analyze_style_confidence_scores()
test_analyze_style_handles_short_documents()
test_analyze_style_handles_multiple_documents()
test_analyze_style_error_on_empty_text()
test_skill_rules_are_actionable()
```

**Module:** `hermes_writer/analysis/style_analyzer.py`

#### 4. LiteLLM Integration Tests
```python
test_litellm_call_with_ollama_provider()
test_litellm_call_with_groq_provider()
test_litellm_fallback_on_provider_failure_when_mode_permits()
test_litellm_retry_with_exponential_backoff()
test_litellm_filters_raw_snippets_before_cloud_send()
test_litellm_error_handling()
test_litellm_timeout_handling()
```

**Module:** `hermes_writer/llm/litellm_client.py`

#### 5. API Request/Response Tests
```python
test_create_profile_request_validation()
test_create_profile_duplicate_id()
test_upload_document_file_size_limit()
test_upload_document_invalid_file_type()
test_generate_content_skill_not_found()
test_generate_content_missing_prompt()
test_api_response_format_on_success()
test_api_response_format_on_error()
test_path_traversal_upload_rejected()
test_malicious_filename_sanitized_or_rejected()
test_cors_rejects_unapproved_origin()
test_error_response_does_not_include_stack_trace()
test_logs_do_not_include_secrets_or_raw_prompts()
```

**Module:** `hermes_writer/api/routes.py`

#### 6. Versioning & Audit Log Tests
```python
test_skill_version_increment()
test_skill_version_saved_separately()
test_rollback_copies_selected_immutable_version_forward()
test_rollback_creates_new_immutable_version()
test_rollback_new_version_status_is_rolled_back()
test_rollback_records_source_version()
test_rollback_records_reason_and_timestamp()
test_rollback_audit_log_records_event_only()
test_audit_log_immutable()
test_audit_log_event_format()
test_audit_log_timestamp_precision()
test_soft_delete_adds_audit_entry()
```

**Module:** `hermes_writer/versioning/skill_versioner.py`, `hermes_writer/audit/audit_logger.py`

#### 7. Privacy & Redaction Tests
```python
test_redact_user_document_before_llm_call()
test_redact_preserves_style_intent()
test_privacy_mode_local_only()
test_privacy_mode_no_cloud_calls()
test_privacy_mode_local_only_fails_closed_on_ollama_failure()
test_privacy_mode_hybrid_allows_controlled_fallback()
test_privacy_mode_cloud_allowed_permits_selected_providers()
test_evidence_snippets_not_sent_to_cloud()
test_user_data_never_logged()
```

**Module:** `hermes_writer/privacy/redactor.py`

---

### Frontend (React / TypeScript)

#### 1. Component Tests

**ProfileSelector.test.tsx**
```typescript
test('renders profile list')
test('selects profile on click')
test('creates new profile with form input')
test('validates profile name (required)')
test('shows error on duplicate profile name')
test('displays profile metadata (created date, skill count)')
```

**DocumentUpload.test.tsx**
```typescript
test('renders drag-and-drop zone')
test('accepts file drop')
test('opens file picker on click')
test('validates file type (PDF, DOCX, TXT)')
test('validates file size (max 50MB)')
test('shows progress bar during upload')
test('displays extraction status')
test('shows preview after extraction')
test('allows manual text editing')
```

**RuleReview.test.tsx**
```typescript
test('renders rule card with description')
test('displays evidence snippets')
test('shows confidence percentage')
test('approves rule on checkbox click')
test('rejects rule on checkbox click')
test('opens edit modal on edit button')
test('allows custom rule addition')
test('saves rule approval state')
test('handles scroll through 20+ rules')
```

**SkillApproval.test.tsx**
```typescript
test('displays skill confirmation details')
test('shows file path where skill is stored')
test('confirms rule counts (approved/rejected/custom)')
test('expands JSON viewer on button click')
test('creates skill on confirmation')
test('cancels without saving on cancel button')
```

**WriteRewrite.test.tsx**
```typescript
test('renders Write tab by default')
test('renders Rewrite tab on click')
test('skill selector dropdown works')
test('prompt field accepts text input')
test('validates prompt length (max 500 chars)')
test('sends generation request on [Generate] click')
test('shows loading state during generation')
test('displays output in preview area')
test('copies output to clipboard')
test('saves output to profile')
test('shows error message on generation failure')
test('Rewrite: accepts original text')
test('Rewrite: shows side-by-side diff on request')
```

#### 2. Hook Tests

**useProfile.test.ts**
```typescript
test('loads profile from localStorage')
test('updates current profile on selection')
test('saves profile changes')
test('handles profile not found error')
test('clears profile on logout (if added)')
```

**useDocuments.test.ts**
```typescript
test('fetches documents for profile')
test('uploads document with progress callback')
test('removes document from list on delete')
test('handles upload failure gracefully')
```

**useSkills.test.ts**
```typescript
test('fetches skills for profile')
test('tracks active skill selection')
test('handles skill not found error')
```

#### 3. Integration Tests (Frontend)

**Profile to Document Flow**
```typescript
test('select profile → upload document → preview extracted text')
test('extracted text updates component state')
test('manual text edit persists in component')
```

**Document to Skill Analysis Flow**
```typescript
test('document list → analyze style → rule review → skill approval')
test('rule approvals update UI state correctly')
test('final skill appears in skill list')
```

#### 4. Performance Tests (Frontend)

```typescript
test('renders large rule list (100 rules) without lag')
test('text preview area smooth scroll with 1M characters')
test('component re-render count on state change')
```

---

## Integration Tests

### Backend

#### 1. File System Workflow
```python
test_upload_document_saves_to_correct_path()
test_extract_document_reads_from_storage()
test_analyze_style_loads_documents_from_storage()
test_create_skill_saves_files_in_correct_structure()
test_rollback_copies_forward_from_immutable_version_file()
test_deletion_marks_file_but_preserves_backup()
```

#### 2. API + Storage Workflow
```python
test_post_profile_creates_directory_and_metadata()
test_post_document_upload_stores_file_and_updates_profile()
test_post_analyze_style_creates_skill_file_and_updates_profile()
test_post_approve_skill_changes_skill_status()
test_post_generate_content_reads_skill_and_calls_llm()
test_get_profile_reflects_all_updates()
```

#### 3. LiteLLM + Storage Workflow
```python
test_generate_content_with_ollama_backend()
test_generate_content_with_cloud_fallback_when_mode_permits()
test_generate_content_local_only_no_cloud_fallback()
test_redaction_before_llm_call()
test_evidence_filtering_before_cloud_llm_call()
test_output_saved_to_storage_after_generation()
```

#### 4. End-to-End Profile Lifecycle
```python
test_create_profile_upload_documents_analyze_create_skill_generate_output()
```

---

## E2E Tests (Playwright - Optional for Phase 1, Priority for Phase 3+)

### Critical User Paths

#### Path 1: New User Onboarding
```typescript
test('new user → create profile → upload document → approve skill → generate content')

// Steps:
// 1. Load app, see Profile Selector
// 2. Fill form: Profile Name = "Alice"
// 3. Click Create Profile
// 4. See empty Dashboard
// 5. Upload PDF (test file)
// 6. See extraction progress, then preview
// 7. Click Next to Analyze
// 8. See rules appear, approve 10 rules
// 9. Click Create Skill
// 10. See new skill in Dashboard
// 11. Click "Use Skill"
// 12. Enter prompt "Write a thank you email"
// 13. Click Generate
// 14. See output generated
// 15. Click Save
// 16. Verify output in Dashboard
```

#### Path 2: Skill Rollback
```typescript
test('create skill v1 -> generate output -> create v2 -> rollback to v1 -> verify new immutable ROLLED_BACK version records source version, reason, and timestamp')
```

#### Path 3: Multi-Document Analysis
```typescript
test('upload 3 documents → analyze style from all 3 → create skill → output reflects combined style')
```

---

## Mocking Strategy

### Backend Mocks

#### LiteLLM Mock
```python
@pytest.fixture
def mock_litellm():
    with patch('hermes_writer.llm.litellm_client.completion') as mock:
        mock.return_value = {
            'choices': [
                {'message': {'content': '{"rules": [...]}'}}
            ]
        }
        yield mock
```

#### File System Mock (Optional, use real tmpdir for most tests)
```python
@pytest.fixture
def temp_profile_dir(tmp_path):
    profile_path = tmp_path / "profiles" / "test_profile"
    profile_path.mkdir(parents=True)
    yield profile_path
```

### Frontend Mocks

#### API Mock
```typescript
vi.mock('@/api/client', () => ({
  uploadDocument: vi.fn().mockResolvedValue({
    doc_id: 'test-001',
    status: 'extracted'
  })
}))
```

#### localStorage Mock
```typescript
const store = {}
const localStorageMock = {
  getItem: (key) => store[key] || null,
  setItem: (key, value) => { store[key] = value }
}
```

---

## Test Data

### Fixtures

#### Document Fixtures
- `sample_letter.pdf` – 1.5KB, 250 words
- `sample_email.txt` – 500B, 80 words
- `large_document.pdf` – 10MB, 50K words
- `corrupted.pdf` – Invalid PDF (for error testing)

#### Skill Fixtures
```json
{
  "skill_id": "test-legal",
  "version": 1,
  "rules": [
    {"rule_id": "rule-001", "category": "tone", "description": "Use formal tone"}
  ]
}
```

#### LLM Response Fixtures
```python
MOCK_STYLE_RULES = {
  "rules": [
    {
      "rule_id": "rule-001",
      "category": "tone",
      "description": "Use professional tone",
      "examples": {...},
      "source_snippets": [...],
      "confidence": 0.92
    }
  ]
}
```

---

## Coverage Requirements

| Module | Target | Tool |
|--------|--------|------|
| `storage/` | 85% | pytest-cov |
| `extraction/` | 80% | pytest-cov |
| `analysis/` | 80% | pytest-cov |
| `api/` | 85% | pytest-cov |
| `llm/` | 80% (with mocks) | pytest-cov |
| `React components` | 80% | vitest + @testing-library/react |
| `React hooks` | 85% | vitest + @testing-library/react |

---

## Contract Tests Required Before Phase 2

### Storage Path Contracts

Tests must assert the exact canonical paths:

| Item | Expected path |
|------|---------------|
| Profile | `data/profiles/{profile_id}/profile.json` |
| Original document | `data/profiles/{profile_id}/documents/original/{filename}` |
| Extracted text | `data/profiles/{profile_id}/documents/extracted/{doc_id}.txt` |
| Document metadata | `data/profiles/{profile_id}/documents/metadata/{doc_id}.json` |
| Active skill | `data/profiles/{profile_id}/skills/{skill_id}/skill.json` |
| Skill version | `data/profiles/{profile_id}/skills/{skill_id}/versions/v{N}.skill.json` |
| Audit log | `data/profiles/{profile_id}/skills/{skill_id}/audit/audit.jsonl` |
| Outputs | `data/profiles/{profile_id}/skills/{skill_id}/outputs/` |

### Privacy Routing Contracts

- Local Only analysis/write/rewrite must call only Ollama.
- Local Only must fail closed when Ollama is unavailable.
- Hybrid may use hosted fallback only after user selection.
- Cloud Allowed may use selected hosted providers only.
- Hosted provider prompts must exclude raw source snippets and raw uploaded document text.

### Security Contracts

- Uploads reject path traversal strings such as `../`.
- Malicious filenames are sanitized or rejected before storage.
- CORS rejects origins other than the approved development frontend origin.
- Logs must not contain API keys, raw uploaded document text, or full prompts.

---

## Test Execution

### Local Development
```bash
# Backend
pytest --cov=hermes_writer --cov-report=html

# Frontend
npm run test:coverage

# E2E (optional)
npm run test:e2e
```

### CI/CD Pipeline
```yaml
test:
  - pytest --cov=hermes_writer --cov-fail-under=80
  - npm run test:coverage -- --coverage --min-coverage 80
  - (optional) npx playwright test
```

---

## Test Maintenance

### Flaky Test Policy
- Rerun flaky tests up to 3 times
- If still failing, investigate root cause
- Document known flaky tests in `KNOWN_ISSUES.md`

### Test Review
- Code review includes test review
- All new features must have tests before merge
- No reduction in coverage allowed

### Test Documentation
- Document complex test logic with comments
- Keep fixture descriptions up-to-date
- Maintain `TEST_README.md` with setup instructions
