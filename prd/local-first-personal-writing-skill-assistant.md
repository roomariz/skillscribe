# Hermes Writer PRD

## Local-First Personal Writing Skill Assistant

### Built on Hermes + LiteLLM + File-Based Storage

## 1. Product Summary

Hermes Writer is a local-first writing assistant that lets a user upload their own documents, extract their writing style, approve a reusable writing skill, and later use that skill to draft or rewrite content.

The system is designed for personal and open-source desktop use. It does not require PostgreSQL, cloud storage, user accounts, or a hosted database.

## 2. Core Architecture

```text
Hermes Writer UI
  ↓
Local Hermes Backend
  ↓
Hermes Skill Engine
  ↓
LiteLLM Proxy
  ↓
Ollama / OpenRouter / Gemini / Groq / Mistral / OpenAI
```

Hermes does not talk directly to model providers.

Hermes only talks to LiteLLM.

LiteLLM handles provider routing.

## 3. Key Design Decision

No SQL database for version 1.

All user data is stored locally as files.

```text
hermes-writer/
  data/
    profiles/
      muhammad/
        profile.json
        skills/
          legal-drafting/
            skill.json
            versions/
              v1.skill.json
              v2.skill.json
            documents/
              original/
                sample-letter.pdf
                sample-email.docx
              extracted/
                sample-letter.txt
                sample-email.txt
            audit/
              audit.jsonl
            outputs/
              draft-001.md
              rewrite-001.md
```

## 4. Why No SQL

PostgreSQL or another database is not needed because the first version is:

* single-user
* local-first
* desktop-style
* open-source friendly
* privacy-focused
* simple to inspect
* easy to back up
* easy to move between machines

A file-based system is better for trust because users can see exactly where their documents, skills, versions, and outputs are stored.

## 5. Storage Model

### Profile File

```json
{
  "profile_id": "muhammad",
  "display_name": "Muhammad",
  "created_at": "2026-05-29T10:00:00Z",
  "default_skill": "legal-drafting"
}
```

### Skill File

```json
{
  "skill_id": "legal-drafting",
  "profile_id": "muhammad",
  "name": "Muhammad Legal Drafting",
  "version": 1,
  "status": "ACTIVE",
  "document_types": ["letter", "email", "submission"],
  "tone_rules": [
    "Use formal British English.",
    "Remain concise, diplomatic and precise."
  ],
  "structure_rules": [
    "Use clear headings where appropriate.",
    "Open with the purpose of the document.",
    "Separate background, issue, analysis and request."
  ],
  "formatting_rules": [
    "Use short paragraphs.",
    "Avoid excessive adjectives.",
    "Use bullet points only where they improve clarity."
  ],
  "opening_patterns": [],
  "closing_patterns": [],
  "preferred_phrases": [],
  "avoid_patterns": [],
  "approved_at": "2026-05-29T10:30:00Z"
}
```

### Audit Log

```jsonl
{"event":"skill_created","skill_id":"legal-drafting","version":1,"timestamp":"2026-05-29T10:00:00Z"}
{"event":"skill_approved","skill_id":"legal-drafting","version":1,"timestamp":"2026-05-29T10:30:00Z"}
{"event":"draft_generated","skill_id":"legal-drafting","output":"draft-001.md","timestamp":"2026-05-29T11:00:00Z"}
```

## 6. LiteLLM Role

LiteLLM is the model gateway.

Hermes sends one OpenAI-compatible request to LiteLLM.

LiteLLM decides which model/provider to use.

```text
Hermes Request
  ↓
LiteLLM
  ↓
Selected Model
```

## 7. Model Routing

### Default Private Mode

```text
Hermes
  ↓
LiteLLM
  ↓
Ollama
  ↓
Local model
```

Used for sensitive personal documents.

### Optional Free Hosted Mode

```text
Hermes
  ↓
LiteLLM
  ↓
OpenRouter / Gemini / Groq
```

Used only if the user enables it.

### Optional Paid Mode

```text
Hermes
  ↓
LiteLLM
  ↓
OpenAI / Anthropic / Mistral paid models
```

Not required for MVP.

## 8. Privacy Modes

The user must choose a privacy mode before generation.

### Local Only

Documents and prompts stay on device.

Only local Ollama models are used.

### Hybrid

Style extraction may be local.

Drafting may use hosted free models.

### Cloud Allowed

User permits selected cloud providers through LiteLLM.

Default should be Local Only.

## 9. Main User Workflows

## Workflow A: Create Style Skill

1. User creates profile.
2. User names the skill.
3. User uploads sample documents.
4. Hermes extracts text locally.
5. Hermes analyses writing style.
6. Hermes creates a proposed skill.
7. User reviews extracted rules.
8. User approves the skill.
9. Skill becomes active.

## Workflow B: Write New Content

Required inputs:

* profile
* skill
* document type
* purpose
* key facts
* any required wording

Hermes loads the approved skill and asks LiteLLM to generate the draft.

## Workflow C: Rewrite Existing Content

Required inputs:

* profile
* skill
* existing content
* desired output type

Hermes preserves meaning and converts the text into the approved style.

## 10. Backend Modules

```text
backend/
  main.py
  services/
    file_store.py
    document_parser.py
    style_analyser.py
    skill_builder.py
    skill_registry.py
    audit_logger.py
    litellm_client.py
    generation_engine.py
    rewrite_engine.py
```

## 11. Frontend Screens

### Home

* Create profile
* Select profile
* View existing skills

### Upload

* Upload documents
* Show extraction status
* Preview extracted text

### Skill Review

* Show tone rules
* Show structure rules
* Show formatting rules
* Show phrases
* Approve or reject skill

### Write

* Select profile
* Select skill
* Select document type
* Enter instructions
* Generate draft

### Rewrite

* Paste existing text
* Select skill
* Convert into user style

### Settings

* LiteLLM endpoint
* default model
* privacy mode
* local-only toggle
* provider keys if user wants cloud models

## 12. File-Based Skill Lifecycle

```text
PENDING
  ↓
APPROVED
  ↓
ACTIVE
  ↓
SUPERSEDED / ROLLED_BACK
```

No skill becomes active automatically.

## 13. Versioning

Each approved change creates a new immutable skill file.

```text
versions/
  v1.skill.json
  v2.skill.json
  v3.skill.json
```

The active skill points to the latest approved version.

Rollback simply changes:

```json
{
  "active_version": 1
}
```

## 14. Safety Rules

Hermes must not:

* silently learn from user documents
* overwrite an active skill without approval
* send documents to cloud models unless user permits it
* treat uploaded documents as legal or factual knowledge
* invent user preferences not found in the uploaded samples
* create a style rule without evidence from the documents

## 15. MVP Scope

Included:

* local profile creation
* document upload
* PDF/DOCX/TXT extraction
* style skill generation
* user approval
* local file-based storage
* LiteLLM integration
* local Ollama route
* optional OpenRouter/Gemini/Groq route
* write new draft
* rewrite existing text
* audit log
* skill rollback

Excluded:

* PostgreSQL
* cloud database
* user login
* team accounts
* collaboration
* real-time editing
* fine-tuning
* automatic continuous learning

## 16. Recommended MVP Stack

Frontend:

* React
* Vite
* Tailwind

Backend:

* FastAPI
* Python

Model Gateway:

* LiteLLM proxy

Local Model Runtime:

* Ollama

Storage:

* local filesystem
* JSON
* JSONL
* Markdown outputs

Parsers:

* PyMuPDF for PDF
* python-docx for DOCX
* built-in text parser for TXT

## 17. Final Architecture

```text
User
 ↓
Hermes Writer UI
 ↓
FastAPI Backend
 ↓
Document Parser
 ↓
Style Analyser
 ↓
Skill Builder
 ↓
Skill Review + Approval
 ↓
Local Skill Store
 ↓
Generation / Rewrite Engine
 ↓
LiteLLM Proxy
 ↓
Selected Model
 ↓
Draft Output
```

## 18. Product Rule

The skill is the product.

The model is replaceable.

LiteLLM makes the model replaceable.

Hermes makes the skill governed.

The local file system makes the product private and open-source friendly.