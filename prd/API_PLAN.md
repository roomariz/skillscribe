# API Plan

## Overview

The Hermes Writer API is a local-first REST API that manages profiles, documents, skills, and content generation. API endpoints are served by FastAPI on `localhost:8000`.

During development the React/Vite frontend runs independently on `localhost:5173`. FastAPI does not serve React during development.

```text
React/Vite dev server
http://localhost:5173
  ↓ HTTP API calls with CORS
FastAPI backend
http://localhost:8000
  ↓ OpenAI-compatible requests
LiteLLM proxy
  ↓ provider routing
Ollama / selected hosted providers
```

## Base URL

```
http://localhost:8000
```

## Canonical Skill Lifecycle

```text
PENDING -> APPROVED -> ACTIVE -> SUPERSEDED
Rollback copy-forwards a prior version into a new ROLLED_BACK version.
```

| Status | Meaning |
|--------|---------|
| PENDING | Proposed skill exists but is not user approved |
| APPROVED | User approved the skill version |
| ACTIVE | Approved version is currently usable |
| SUPERSEDED | Version was replaced by a newer active version |
| ROLLED_BACK | New copy-forward version created from an earlier version |

## Privacy Routing Matrix

| Privacy Mode | API value | Allowed providers | Failure behavior |
|--------------|-----------|-------------------|------------------|
| Local Only | `local_only` | Ollama only | Fail closed; no cloud call |
| Hybrid | `hybrid` | Ollama, then selected hosted providers | Controlled fallback only after user selection |
| Cloud Allowed | `cloud_allowed` | Selected hosted providers through LiteLLM | Cloud routing permitted |

Cloud-routed requests must not include raw document snippets. They may include approved style rules, abstractions, and summaries.

## Canonical Storage Paths Used By API

| Resource | Path |
|----------|------|
| Profile | `data/profiles/{profile_id}/profile.json` |
| Original document | `data/profiles/{profile_id}/documents/original/{filename}` |
| Extracted text | `data/profiles/{profile_id}/documents/extracted/{doc_id}.txt` |
| Document metadata | `data/profiles/{profile_id}/documents/metadata/{doc_id}.json` |
| Skill | `data/profiles/{profile_id}/skills/{skill_id}/skill.json` |
| Version | `data/profiles/{profile_id}/skills/{skill_id}/versions/v{N}.skill.json` |
| Audit log | `data/profiles/{profile_id}/skills/{skill_id}/audit/audit.jsonl` |
| Outputs | `data/profiles/{profile_id}/skills/{skill_id}/outputs/` |

## Response Format

All responses are JSON with consistent structure:

### Success Response (2xx)
```json
{
  "success": true,
  "data": {
    // ... response payload
  },
  "timestamp": "2026-05-29T10:00:00Z"
}
```

### Error Response (4xx, 5xx)
```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "message": "Human-readable error message",
  "timestamp": "2026-05-29T10:00:00Z",
  "details": {
    // Optional additional details
  }
}
```

---

## Profile Endpoints

### Create Profile
```
POST /api/profiles
```

**Request Body:**
```json
{
  "profile_id": "muhammad",
  "display_name": "Muhammad",
  "description": "Optional profile description"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "profile_id": "muhammad",
    "display_name": "Muhammad",
    "created_at": "2026-05-29T10:00:00Z",
    "default_skill": null
  }
}
```

### List Profiles
```
GET /api/profiles
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "profile_id": "muhammad",
      "display_name": "Muhammad",
      "created_at": "2026-05-29T10:00:00Z",
      "default_skill": "legal-drafting",
      "skill_count": 3,
      "document_count": 5
    }
  ]
}
```

### Get Profile
```
GET /api/profiles/{profile_id}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "profile_id": "muhammad",
    "display_name": "Muhammad",
    "created_at": "2026-05-29T10:00:00Z",
    "default_skill": "legal-drafting",
    "skills": [
      {"skill_id": "legal-drafting", "name": "Legal Drafting", "version": 1, "status": "ACTIVE"}
    ],
    "documents": [
      {"doc_id": "doc-001", "filename": "sample.pdf", "uploaded_at": "2026-05-29T10:00:00Z", "status": "extracted"}
    ]
  }
}
```

### Update Profile
```
PUT /api/profiles/{profile_id}
```

**Request Body:**
```json
{
  "display_name": "Muhammad Ali",
  "default_skill": "legal-drafting"
}
```

**Response (200):** Updated profile object

### Delete Profile
```
DELETE /api/profiles/{profile_id}
```

**Response (204):** No content

---

## Document Endpoints

### Upload Document
```
POST /api/profiles/{profile_id}/documents/upload
```

**Content-Type:** `multipart/form-data`

**Request:**
- File: `file` (PDF, DOCX, or TXT)
- Optional: `tags` (comma-separated string)

**Response (202 - Processing):**
```json
{
  "success": true,
  "data": {
    "doc_id": "doc-001",
    "filename": "sample.pdf",
    "status": "extracting",
    "progress": 0.5,
    "estimated_time_seconds": 15
  }
}
```

### Get Document
```
GET /api/profiles/{profile_id}/documents/{doc_id}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "doc_id": "doc-001",
    "filename": "sample.pdf",
    "status": "extracted",
    "uploaded_at": "2026-05-29T10:00:00Z",
    "extracted_text": "...",
    "word_count": 1250,
    "character_count": 8500,
    "extraction_method": "pymupdf"
  }
}
```

### List Documents
```
GET /api/profiles/{profile_id}/documents
```

**Query Params:**
- `status` (optional): `uploading`, `extracting`, `extracted`, `error`

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "doc_id": "doc-001",
      "filename": "sample.pdf",
      "status": "extracted",
      "uploaded_at": "2026-05-29T10:00:00Z",
      "word_count": 1250
    }
  ]
}
```

### Update Extracted Text
```
PUT /api/profiles/{profile_id}/documents/{doc_id}
```

**Request Body:**
```json
{
  "extracted_text": "Manually corrected text..."
}
```

**Response (200):** Updated document object

### Delete Document
```
DELETE /api/profiles/{profile_id}/documents/{doc_id}
```

**Response (204):** No content

---

## Style Analysis Endpoints

### Analyze Style
```
POST /api/profiles/{profile_id}/analyze-style
```

**Request Body:**
```json
{
  "document_ids": ["doc-001", "doc-002"],
  "skill_name": "Muhammad Legal Drafting",
  "description": "Optional analysis description"
}
```

**Response (202 - Processing):**
```json
{
  "success": true,
  "data": {
    "analysis_id": "analysis-001",
    "status": "analyzing",
    "progress": 0.0,
    "estimated_time_seconds": 60
  }
}
```

### Get Analysis Status
```
GET /api/profiles/{profile_id}/analyze-style/{analysis_id}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "analysis_id": "analysis-001",
    "status": "completed",
    "rules": [
      {
        "rule_id": "rule-001",
        "category": "tone",
        "description": "Use professional but approachable tone",
        "source": "document_derived",
        "evidence": ["doc-001#snippet-001"],
        "examples": {
          "positive": "We appreciate your business.",
          "negative": "You must comply."
        },
        "source_snippets": ["...", "..."],
        "confidence": 0.92
      }
    ]
  }
}
```

### Approve/Reject Rules
```
POST /api/profiles/{profile_id}/analyze-style/{analysis_id}/approve
```

**Request Body:**
```json
{
  "approved_rules": ["rule-001", "rule-002"],
  "rejected_rules": ["rule-003"],
  "custom_rules": [
    {
      "category": "structure",
      "description": "Always include headings",
      "source": "user_authored",
      "evidence": null,
      "examples": {
        "positive": "## Section Title",
        "negative": "Section Title (without heading)"
      }
    }
  ]
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "skill_id": "legal-drafting",
    "version": 1,
    "status": "PENDING",
    "rules_count": 15
  }
}
```

---

## Skill Endpoints

### List Skills
```
GET /api/profiles/{profile_id}/skills
```

**Query Params:**
- `status` (optional): `PENDING`, `APPROVED`, `ACTIVE`, `SUPERSEDED`, `ROLLED_BACK`

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "skill_id": "legal-drafting",
      "name": "Legal Drafting",
      "version": 2,
      "status": "ACTIVE",
      "rules_count": 15,
      "created_at": "2026-05-29T10:00:00Z",
      "updated_at": "2026-05-29T11:00:00Z"
    }
  ]
}
```

### Get Skill
```
GET /api/profiles/{profile_id}/skills/{skill_id}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "skill_id": "legal-drafting",
    "name": "Legal Drafting",
    "version": 2,
    "status": "ACTIVE",
    "rules": [
      {
        "rule_id": "rule-001",
        "category": "tone",
        "description": "Use professional tone",
        "examples": { ... }
      }
    ],
    "versions": [
      {"version": 2, "created_at": "2026-05-29T11:00:00Z", "status": "ACTIVE"},
      {"version": 1, "created_at": "2026-05-29T10:00:00Z", "status": "SUPERSEDED"}
    ]
  }
}
```

### Approve Skill
```
POST /api/profiles/{profile_id}/skills/{skill_id}/approve
```

**Response (200):** Updated skill object with status `ACTIVE`

### Rollback Skill Version
```
POST /api/profiles/{profile_id}/skills/{skill_id}/rollback
```

**Request Body:**
```json
{
  "version": 1,
  "reason": "Version 2 had too many false positives"
}
```

**Response (201):** New skill object with incremented version, status `ROLLED_BACK`, and `rolled_back_from_version` set to the requested source version.

### Delete Skill
```
DELETE /api/profiles/{profile_id}/skills/{skill_id}
```

**Response (204):** No content

### Get Skill Audit Log
```
GET /api/profiles/{profile_id}/skills/{skill_id}/audit
```

**Query Params:**
- `limit` (optional, default 100)
- `offset` (optional, default 0)

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2026-05-29T11:00:00Z",
      "event_type": "skill_approved",
      "actor": "user",
      "details": { }
    }
  ]
}
```

---

## Content Generation Endpoints

### Write (Generate New Content)
```
POST /api/profiles/{profile_id}/write
```

**Request Body:**
```json
{
  "skill_id": "legal-drafting",
  "prompt": "Draft a thank you letter to a client",
  "context": "Optional context or outline",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Response (202 - Processing):**
```json
{
  "success": true,
  "data": {
    "generation_id": "gen-001",
    "status": "generating",
    "progress": 0.0
  }
}
```

### Get Generation Status
```
GET /api/profiles/{profile_id}/generations/{generation_id}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "generation_id": "gen-001",
    "status": "completed",
    "content": "...",
    "skill_id": "legal-drafting",
    "skill_version": 2,
    "model": "mistral-7b",
    "created_at": "2026-05-29T11:00:00Z",
    "output_id": "draft-001",
    "output_path": "data/profiles/muhammad/skills/legal-drafting/outputs/draft-001.md"
  }
}
```

### Rewrite (Apply Style to Existing Text)
```
POST /api/profiles/{profile_id}/rewrite
```

**Request Body:**
```json
{
  "skill_id": "legal-drafting",
  "original_text": "Text to be rewritten...",
  "instructions": "Optional rewrite instructions",
  "temperature": 0.5
}
```

**Response (202):** Same as write endpoint

### List Outputs
```
GET /api/profiles/{profile_id}/outputs
```

**Query Params:**
- `skill_id` (optional)
- `type` (optional): `write`, `rewrite`
- `limit` (optional, default 50)

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "output_id": "draft-001",
      "type": "write",
      "skill_id": "legal-drafting",
      "prompt": "Draft a thank you letter",
      "created_at": "2026-05-29T11:00:00Z",
      "preview": "Dear Client..."
    }
  ]
}
```

### Get Output
```
GET /api/profiles/{profile_id}/outputs/{output_id}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "output_id": "draft-001",
    "type": "write",
    "content": "...",
    "skill_id": "legal-drafting",
    "skill_version": 2,
    "created_at": "2026-05-29T11:00:00Z"
  }
}
```

---

## Configuration Endpoints

### Get Config
```
GET /api/config
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "providers": [
      {"name": "ollama", "available": true, "model": "mistral"},
      {"name": "groq", "available": true},
      {"name": "mistral", "available": false}
    ],
    "privacy_mode": "local_only",
    "max_upload_size_mb": 50,
    "storage_path": "./data"
  }
}
```

### Test Provider Connection
```
POST /api/config/test-provider
```

**Request Body:**
```json
{
  "provider": "groq"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "provider": "groq",
    "connected": true,
    "model": "mixtral-8x7b-32768"
  }
}
```

### Update Privacy Mode
```
POST /api/config/update-privacy-mode
```

**Request Body:**
```json
{
  "privacy_mode": "local_only"
}
```

**Valid values:** `local_only`, `hybrid`, `cloud_allowed`

**Response (200):** Updated config. If `local_only` is selected, all LLM operations must be restricted to Ollama and must fail closed when Ollama is unavailable.

---

## Health & Status Endpoints

### Health Check
```
GET /health
```

**Response (200):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "storage_available": true,
  "profiles_count": 3
}
```

### System Status
```
GET /api/status
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "storage_path": "./data",
    "storage_used_mb": 125.5,
    "storage_available_mb": 5000.0,
    "database_type": "file-based",
    "profiles_count": 3,
    "documents_count": 15,
    "skills_count": 5
  }
}
```

---

## Error Codes

| Error Code | HTTP | Description |
|-----------|------|-------------|
| `PROFILE_NOT_FOUND` | 404 | Profile does not exist |
| `DOCUMENT_NOT_FOUND` | 404 | Document does not exist |
| `SKILL_NOT_FOUND` | 404 | Skill does not exist |
| `INVALID_REQUEST` | 400 | Request validation failed |
| `FILE_UPLOAD_FAILED` | 400 | File upload error |
| `EXTRACTION_FAILED` | 500 | Document text extraction failed |
| `ANALYSIS_FAILED` | 500 | Style analysis failed |
| `GENERATION_FAILED` | 500 | Content generation failed |
| `PROVIDER_UNAVAILABLE` | 503 | LLM provider not available |
| `STORAGE_ERROR` | 500 | File storage error |

---

## Rate Limiting

No rate limiting in Phase 1 (single-user, local-only).
