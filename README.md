# Hermes Writer

Local-first personal writing skill assistant. Sprint 1 is a scaffold only: FastAPI, React/Vite, configuration, local file storage primitives, API envelopes, health/status endpoints, and tests.

## Requirements

- Python 3.10+
- Node 18+

## Backend

```bash
python -m pip install -r requirements-dev.txt
uvicorn hermes_writer.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Health: `http://localhost:8000/health`
Swagger: `http://localhost:8000/docs`

## Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Frontend: `http://localhost:5173`

## Tests

```bash
pytest
cd frontend
npm test
npm run build
```

## Scope Guard

This sprint intentionally does not implement upload, extraction, style analysis, skill creation, LiteLLM generation, rollback, authentication, SQL, cloud databases, credential-write APIs, or automatic learning.

