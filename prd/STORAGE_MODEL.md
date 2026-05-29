# Storage Model

## Design Principles

1. **File-First:** All data stored as JSON files on local disk
2. **Transparent:** Users can inspect all files directly
3. **Atomic:** Writes use temp file + rename (no corruption)
4. **Versioned:** All changes preservable via audit logs
5. **Portable:** Easy to backup, move, or inspect offline
6. **No SQL:** No database required for Phase 1

---

## Directory Structure

```
hermes-writer/
├── data/
│   ├── profiles/
│   │   ├── {profile_id}/
│   │   │   ├── profile.json
│   │   │   ├── documents/
│   │   │   │   ├── original/
│   │   │   │   │   ├── {filename} (original files)
│   │   │   │   │   └── ...
│   │   │   │   ├── extracted/
│   │   │   │   │   ├── {doc_id}.txt
│   │   │   │   │   └── ...
│   │   │   │   └── metadata/
│   │   │   │       ├── {doc_id}.json
│   │   │   │       └── ...
│   │   │   ├── skills/
│   │   │   │   ├── {skill_id}/
│   │   │   │   │   ├── skill.json (active version)
│   │   │   │   │   ├── versions/
│   │   │   │   │   │   ├── v1.skill.json
│   │   │   │   │   │   ├── v2.skill.json
│   │   │   │   │   │   └── ...
│   │   │   │   │   ├── audit/
│   │   │   │   │   │   └── audit.jsonl (immutable log)
│   │   │   │   │   ├── outputs/
│   │   │   │   │   │   ├── draft-{id}.md
│   │   │   │   │   │   ├── rewrite-{id}.md
│   │   │   │   │   │   └── ...
│   │   │   │   │   └── metadata.json (version history)
│   │   │   │   └── ...
│   │   └── ...
│   └── .version (storage format version)
└── logs/
    └── error.log (optional)
```

---

## Canonical Lifecycle

```text
PENDING
  ↓
APPROVED
  ↓
ACTIVE
  ↓
SUPERSEDED

Rollback creates a new immutable version with status ROLLED_BACK.
```

| From | To | Trigger | Storage effect |
|------|----|---------|----------------|
| PENDING | APPROVED | User approves proposed skill rules | Version file is written |
| APPROVED | ACTIVE | User activates a skill | `skill.json` points to active version |
| ACTIVE | SUPERSEDED | Newer version becomes active | Previous active version is marked SUPERSEDED |
| ACTIVE | ROLLED_BACK | User rolls back | Earlier version is copied forward as a new version |
| SUPERSEDED | ROLLED_BACK | User restores an older version | Older version is copied forward as a new version |

## Storage Path Consistency Table

| Item | Canonical path |
|------|----------------|
| Profile | `data/profiles/{profile_id}/profile.json` |
| Original document | `data/profiles/{profile_id}/documents/original/{filename}` |
| Extracted text | `data/profiles/{profile_id}/documents/extracted/{doc_id}.txt` |
| Document metadata | `data/profiles/{profile_id}/documents/metadata/{doc_id}.json` |
| Active skill | `data/profiles/{profile_id}/skills/{skill_id}/skill.json` |
| Skill version | `data/profiles/{profile_id}/skills/{skill_id}/versions/v{N}.skill.json` |
| Version metadata | `data/profiles/{profile_id}/skills/{skill_id}/metadata.json` |
| Audit log | `data/profiles/{profile_id}/skills/{skill_id}/audit/audit.jsonl` |
| Outputs | `data/profiles/{profile_id}/skills/{skill_id}/outputs/` |

---

## File Format Specifications

### Profile File

**Path:** `data/profiles/{profile_id}/profile.json`

**Schema:**
```json
{
  "profile_id": "string (unique slug or UUID)",
  "display_name": "string",
  "description": "string (optional)",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp",
  "default_skill": "string (skill_id, optional)",
  "metadata": {
    "total_documents": "integer",
    "total_skills": "integer",
    "backup_location": "string (optional)"
  }
}
```

**Example:**
```json
{
  "profile_id": "muhammad",
  "display_name": "Muhammad",
  "description": "Personal writing profile for legal drafting",
  "created_at": "2026-05-29T10:00:00Z",
  "updated_at": "2026-05-29T10:00:00Z",
  "default_skill": "legal-drafting",
  "metadata": {
    "total_documents": 5,
    "total_skills": 2
  }
}
```

---

### Document Metadata File

**Path:** `data/profiles/{profile_id}/documents/metadata/{doc_id}.json`

**Schema:**
```json
{
  "doc_id": "string (UUID)",
  "profile_id": "string",
  "original_filename": "string",
  "file_type": "pdf|docx|txt",
  "file_size_bytes": "integer",
  "uploaded_at": "ISO 8601 timestamp",
  "extraction_started_at": "ISO 8601 timestamp",
  "extraction_completed_at": "ISO 8601 timestamp",
  "extraction_method": "pymupdf|python-docx|plain-text",
  "extracted_text_location": "string (relative path)",
  "word_count": "integer",
  "character_count": "integer",
  "status": "uploading|extracting|extracted|error",
  "error_message": "string (optional)"
}
```

**Example:**
```json
{
  "doc_id": "doc-001",
  "profile_id": "muhammad",
  "original_filename": "sample-letter.pdf",
  "file_type": "pdf",
  "file_size_bytes": 2500,
  "uploaded_at": "2026-05-29T10:00:00Z",
  "extraction_completed_at": "2026-05-29T10:05:00Z",
  "extraction_method": "pymupdf",
  "extracted_text_location": "extracted/doc-001.txt",
  "word_count": 250,
  "character_count": 1500,
  "status": "extracted"
}
```

---

### Extracted Text File

**Path:** `data/profiles/{profile_id}/documents/extracted/{doc_id}.txt`

**Format:** Plain UTF-8 text (preserved line breaks)

**Example:**
```
Dear Client,

We appreciate your business and want to ensure the highest standards 
of service. Our team is committed to your success.

Best regards,
Muhammad
```

---

### Skill File (Active Version)

**Path:** `data/profiles/{profile_id}/skills/{skill_id}/skill.json`

**Schema:**
```json
{
  "skill_id": "string",
  "profile_id": "string",
  "name": "string",
  "description": "string (optional)",
  "version": "integer",
  "status": "PENDING|APPROVED|ACTIVE|SUPERSEDED|ROLLED_BACK",
  "created_at": "ISO 8601 timestamp",
  "approved_at": "ISO 8601 timestamp (optional)",
  "source_documents": ["doc_id", ...],
  "rules": [
    {
      "rule_id": "string (UUID)",
      "category": "tone|structure|vocabulary|formality|other",
      "title": "string",
      "description": "string",
      "examples": {
        "positive": "string",
        "negative": "string"
      },
      "source": "document_derived|user_authored",
      "evidence": "array or null",
      "source_snippets": ["string", ...],
      "confidence": "number (0-1)",
      "user_edited": "boolean",
      "user_edit_note": "string (optional)"
    }
  ],
  "metadata": {
    "total_rules": "integer",
    "approved_rules": "integer",
    "rejected_rules": "integer",
    "custom_rules": "integer",
    "analysis_duration_seconds": "number"
  }
}
```

**Example:**
```json
{
  "skill_id": "legal-drafting",
  "profile_id": "muhammad",
  "name": "Muhammad Legal Drafting",
  "description": "Style for legal documents and formal correspondence",
  "version": 2,
  "status": "ACTIVE",
  "created_at": "2026-05-29T10:10:00Z",
  "approved_at": "2026-05-29T10:15:00Z",
  "source_documents": ["doc-001", "doc-002"],
  "rules": [
    {
      "rule_id": "rule-001",
      "category": "tone",
      "title": "Professional Tone",
      "description": "Use professional but approachable tone in all correspondence",
      "examples": {
        "positive": "We appreciate your business and value our partnership.",
        "negative": "You must comply immediately."
      },
      "source": "document_derived",
      "evidence": [
        "doc-001#snippet-001",
        "doc-002#snippet-003"
      ],
      "source_snippets": [
        "We appreciate your business and want to ensure...",
        "Thank you for your continued trust..."
      ],
      "confidence": 0.92,
      "user_edited": false
    }
  ],
  "metadata": {
    "total_rules": 15,
    "approved_rules": 14,
    "rejected_rules": 1,
    "custom_rules": 0,
    "analysis_duration_seconds": 45.2
  }
}
```

---

### Skill Version File

**Path:** `data/profiles/{profile_id}/skills/{skill_id}/versions/v{N}.skill.json`

**Schema:** Same as active skill.json

**Example:** `v1.skill.json`, `v2.skill.json`

---

### User-Authored Custom Rule Example

Custom rules are allowed only when their provenance is explicit. They are not treated as document-derived evidence.

```json
{
  "rule_id": "rule-custom-001",
  "category": "structure",
  "title": "Always Include Headings",
  "description": "Use clear headings for each major section.",
  "examples": {
    "positive": "## Background",
    "negative": "A long unheaded paragraph"
  },
  "source": "user_authored",
  "evidence": null,
  "source_snippets": [],
  "confidence": 1.0,
  "user_edited": true,
  "user_edit_note": "Added manually by user during skill review."
}
```

---

### Version Metadata File

**Path:** `data/profiles/{profile_id}/skills/{skill_id}/metadata.json`

**Schema:**
```json
{
  "skill_id": "string",
  "current_version": "integer",
  "versions": [
    {
      "version": "integer",
      "created_at": "ISO 8601 timestamp",
      "status": "PENDING|APPROVED|ACTIVE|SUPERSEDED|ROLLED_BACK",
      "change_summary": "string",
      "rules_count": "integer",
      "rolled_back_from_version": "integer (only for ROLLED_BACK versions)"
    }
  ]
}
```

**Example:**
```json
{
  "skill_id": "legal-drafting",
  "current_version": 2,
  "versions": [
    {
      "version": 2,
      "created_at": "2026-05-29T10:15:00Z",
      "status": "ACTIVE",
      "change_summary": "Added vocabulary rule for formal language",
      "rules_count": 15
    },
    {
      "version": 1,
      "created_at": "2026-05-29T10:10:00Z",
      "status": "SUPERSEDED",
      "change_summary": "Initial skill from documents",
      "rules_count": 14
    }
  ]
}
```

---

### Rollback Lifecycle Example

If version 2 is ACTIVE and the user rolls back to version 1, rollback creates version 3:

```json
{
  "version": 3,
  "status": "ROLLED_BACK",
  "rolled_back_from_version": 1,
  "change_summary": "Copy-forward rollback to version 1"
}
```

The previous ACTIVE version becomes SUPERSEDED. Version 1 remains immutable.

---

### Audit Log File (Immutable)

**Path:** `data/profiles/{profile_id}/skills/{skill_id}/audit/audit.jsonl`

**Format:** JSON Lines (one JSON object per line, immutable append-only)

**Schema (each line):**
```json
{
  "timestamp": "ISO 8601 timestamp",
  "event_type": "skill_created|rule_approved|rule_rejected|skill_approved|skill_rollback|skill_deleted",
  "actor": "user|system",
  "skill_version": "integer (optional)",
  "details": {
    // Event-specific details
  }
}
```

**Example:**
```jsonl
{"timestamp":"2026-05-29T10:10:00Z","event_type":"skill_created","actor":"user","skill_version":1,"details":{"rule_count":14}}
{"timestamp":"2026-05-29T10:12:00Z","event_type":"rule_rejected","actor":"user","skill_version":1,"details":{"rule_id":"rule-005","reason":"Not applicable"}}
{"timestamp":"2026-05-29T10:15:00Z","event_type":"skill_approved","actor":"user","skill_version":1,"details":{}}
{"timestamp":"2026-05-29T10:20:00Z","event_type":"skill_created","actor":"system","skill_version":2,"details":{"change":"Added vocabulary rule"}}
{"timestamp":"2026-05-29T10:22:00Z","event_type":"skill_approved","actor":"user","skill_version":2,"details":{}}
```

---

### Output File (Generated Content)

**Path:** `data/profiles/{profile_id}/skills/{skill_id}/outputs/draft-{id}.md` or `rewrite-{id}.md`

**Format:** Markdown with YAML frontmatter

**Schema:**
```markdown
---
output_id: string
output_type: write|rewrite
skill_id: string
skill_version: integer
model: string
created_at: ISO 8601 timestamp
generation_duration_seconds: number
prompt: string (for write)
original_text: string (for rewrite, optional)
instructions: string (for rewrite, optional)
---

# Generated Content

[Content here]
```

**Example:**
```markdown
---
output_id: draft-001
output_type: write
skill_id: legal-drafting
skill_version: 2
model: mistral-7b
created_at: 2026-05-29T10:30:00Z
generation_duration_seconds: 8.5
prompt: Draft a thank you letter to a client for referring new business
---

Dear John,

Thank you for referring Sarah Mitchell to our firm. We greatly appreciate 
your confidence in our services and are committed to delivering the highest 
standards of work for this engagement.

Best regards,
Muhammad
```

---

### Version Control File

**Path:** `data/.version`

**Format:** Plain text

**Content:**
```
storage_format_version=1
hermes_writer_version=1.0.0
```

---

## Storage Operations

### Write Atomicity

All writes use the **temp file + atomic rename** pattern:

```python
def write_json_atomic(file_path, data):
    # 1. Create temp file
    temp_path = f"{file_path}.tmp"
    
    # 2. Write to temp
    with open(temp_path, 'w') as f:
        json.dump(data, f)
    
    # 3. Atomic rename (POSIX atomic on all major OS)
    os.replace(temp_path, file_path)
```

This prevents file corruption if process crashes mid-write.

### File Locking

For concurrent read/write scenarios:

```python
import fcntl  # Unix
import msvcrt  # Windows

def write_with_lock(file_path, data):
    with open(file_path, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
        try:
            json.dump(data, f)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
```

### Backup Before Modifications

```python
def backup_before_write(file_path):
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
    return backup_path
```

### Recovery from Partial Writes

```python
def recover_from_backup(file_path):
    backup_path = f"{file_path}.backup"
    if os.path.exists(backup_path) and not os.path.exists(file_path):
        shutil.copy2(backup_path, file_path)
        return True
    return False
```

---

## Data Integrity

### JSON Validation

All JSON files validated against schema on read:

```python
def read_json_validated(file_path, schema):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Validate against schema
    jsonschema.validate(data, schema)
    return data
```

### Audit Log Immutability

Audit log is append-only:

```python
def append_audit_entry(audit_path, event):
    with open(audit_path, 'a') as f:
        f.write(json.dumps(event) + '\n')
    
    # Verify written
    with open(audit_path, 'r') as f:
        lines = f.readlines()
        assert lines[-1].strip() == json.dumps(event)
```

### Rollback Verification

Before rollback, verify version file exists:

```python
def rollback_safe(skill_id, target_version):
    version_file = f"versions/v{target_version}.skill.json"
    if not os.path.exists(version_file):
        raise FileNotFoundError(f"Version {target_version} not found")
    
    # Load and verify
    skill = read_json_validated(version_file, SKILL_SCHEMA)
    
    # Copy forward into a new immutable version with status ROLLED_BACK
    shutil.copy2(version_file, "skill.json")
    
    # Log event
    append_audit_entry(f"rollback copy-forward from v{target_version}")
```

---

## Scale Limits (Phase 1)

| Item | Limit | Rationale |
|------|-------|-----------|
| Profiles per installation | 10 | Single-user, rare multi-user on same machine |
| Documents per profile | 1000 | Practical for individual |
| Skills per profile | 100 | Each skill is small (< 100KB) |
| Rules per skill | 50 | LLM-generated, reasonable limit |
| Output files per profile | 10000 | Pruned or compressed over time |
| Total data per profile | 5GB | Typical disk space |

**Phase 1 constraint:** Keep file-based storage. No SQL database is part of the MVP planning package.

---

## Backup & Portability

### Manual Backup
```bash
# Entire profile
tar czf backup-muhammad-$(date +%Y%m%d).tar.gz data/profiles/muhammad/

# Single skill with versions
tar czf backup-legal-drafting-$(date +%Y%m%d).tar.gz \
  data/profiles/muhammad/skills/legal-drafting/
```

### Restore
```bash
tar xzf backup-muhammad-20260529.tar.gz
```

### Cross-Machine Migration
1. Backup `data/profiles/{profile_id}/` on source machine
2. Transfer `.tar.gz` to target machine
3. Extract in target `data/profiles/`
4. Restart Hermes Writer
5. Profile automatically detected and loaded

---

## Privacy Assumptions

- All files are user-readable (no encryption in Phase 1)
- No files uploaded to cloud
- No telemetry collected
- Audit logs only contain local events
- User is trusted to safeguard `data/` directory

---

## Future Enhancements (Phase 2+)

- **Encryption:** Encrypt sensitive data at rest (AES-256)
- **Compression:** Compress superseded outputs
- **Deduplication:** Content-address-based dedup for large documents
