# Hermes Writer Architecture

Sprint 1 establishes two separate local services:

```text
React/Vite UI
http://localhost:5173
  -> JSON API calls with CORS
FastAPI backend
http://localhost:8000
  -> local filesystem under ./data
```

FastAPI does not serve React during development. The backend initializes `data/.version` and `data/profiles/` on startup, exposes `/health`, `/api/status`, and `/api/version`, and returns structured JSON error envelopes.

All canonical paths are resolved through `PathRegistry`. Storage writes use temp-file plus atomic rename, and write-critical code can use the cross-platform file lock helper.

No SQL database, login/auth, cloud database, direct provider calls, document upload, extraction, skills, generation, rollback, or automatic learning exists in Sprint 1.

