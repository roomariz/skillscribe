# Contributing

## Local Development

1. Copy `.env.example` to `.env` for local overrides.
2. Install backend dev dependencies with `python -m pip install -r requirements-dev.txt`.
3. Install frontend dependencies from `frontend/` with `npm install`.
4. Run `pytest`, `npm test`, and `npm run build` before handing off changes.

## Data Safety

Local user data belongs under `data/`, which is ignored by git. Do not add credential-write endpoints, direct provider SDK calls, SQL migrations, or cloud storage in this local-first MVP.

