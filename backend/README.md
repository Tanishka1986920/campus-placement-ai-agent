Backend Agent (Campus Placement AI)

This backend implements a minimal FastAPI application intended for the Campus Placement AI project. It includes endpoints for resume upload/processing and simple student queries.

IMPORTANT: repository layout and running instructions
- All backend sources live under the backend/ directory. To run or test locally from the repo root you must change into the backend/ directory first.
  Example:
    cd backend
    uvicorn app.main:app --reload --port 8000
    pytest -q

Tech stack
- Python 3.11+
- FastAPI
- Uvicorn (ASGI server)
- Pydantic for validation
- Pytest for tests

Quickstart (from backend/)
- Install deps: pip install -r requirements.txt
- Run app locally: uvicorn app.main:app --reload --port 8000
- Run tests: pytest -q

Notes about CI in this repository
- The existing repository-level CI must run tests from backend/ (cd backend && pytest -q) or adjust PYTHONPATH to include backend/. If CI currently runs pytest from repo root, update the workflow to change directory into backend/ before running pytest.

Important operational notes
- This implementation uses in-memory stores (RESUME_STORE). For production replace this with durable storage (S3 / blob store / database).
- Secrets and configuration must be provided via environment variables (DO NOT commit secrets).

Files and layout (inside backend/)
- app/main.py - FastAPI application
- services/foundry_adapter.py - Foundry adapter interface + mock
- services/github_adapter.py - GitHub adapter (mockable) to claim/operate on GitHub issues (requires GITHUB_TOKEN env var for real usage)
- tests/ - pytest tests
- docs/integrations.md - describes message formats and webhook/task schemas for multi-agent integrations
- requirements.txt - pinned minimal dependencies for reproducible CI

Environment variables (example in .env.example)
- FOUNDRY_BASE_URL - (optional) Foundry service base URL
- FOUNDRY_CLIENT_ID - (optional) Foundry client id
- FOUNDRY_CLIENT_SECRET - (optional) Foundry client secret
- GITHUB_TOKEN - (optional) token used by services/github_adapter.py to operate on GitHub issues
- STORAGE_URL, STORAGE_KEY - optional storage backend credentials

Agent metadata and responsibilities
- The Backend Agent owns backend development tasks: implementing Python/FastAPI endpoints, validation, error handling, integrations with Microsoft Foundry, writing tests, CI configuration, and handing off completed work to the Bug/Issue Agent for verification.

Limitations
- Auth is out-of-scope for this iteration but a placeholder rate-limiter is implemented. See code and TODOs for next steps.
