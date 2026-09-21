Integrations and multi-agent contracts

This document describes the minimal message formats and webhook/task-queue conventions used by the Backend Agent to interact with Microsoft Foundry and other agents.

1) Resume processing submission (Backend -> Foundry)
- Endpoint: Foundry API (adapter abstracts details)
- Payload (example JSON):
  {
    "resume_id": "<uuid>",
    "filename": "resume.pdf",
    "content_length": 12345,
    "content_type": "application/pdf",
    "submitted_at": 1690000000.123,
    "callback_url": "https://backend.example.com/api/integrations/foundry/callback"
  }
- Notes: file bytes are usually sent as multipart or a pre-signed storage URL. The FoundryAdapter should return a task_id.

2) Foundry task status polling (Backend -> Foundry)
- Adapter should expose get_task_status(task_id) returning:
  {
    "task_id": "<id>",
    "status": "submitted|running|completed|failed",
    "updated_at": 1690000010.0,
    "result": { ... }  # optional parsed resume content or pointers to storage
  }

3) Foundry -> Backend webhook (push model)
- When Foundry completes processing, it may POST to backend callback:
  POST /api/integrations/foundry/callback
  Headers: X-Signature or similar (optional)
  Body JSON example:
  {
    "task_id": "<id>",
    "resume_id": "<uuid>",
    "status": "completed",
    "result_url": "https://storage.example.com/resume-results/<uuid>.json",
    "result": { "parsed": {...}, "score": 0.72 }
  }
- Backend should verify signature if provided and then update internal resume storage and notify Bug/Issue Agent if necessary.

4) Correlation / tracing
- All inter-agent messages should include a correlation_id. If absent, the receiver must generate one and include it in responses.
- Use header X-Correlation-ID for HTTP messages.

5) Claims & issue workflow (Backend Agent <-> Bug/Issue Agent / GitHub)
- When the Backend Agent claims an issue, it should post a comment and assign itself (or a designated service account) using the GitHub Adapter.
- Example comment body:
  "Claiming this backend task for implementation. Backend Agent will implement endpoint(s) and add tests. Correlation ID: <id>"

6) Local dev / test adapters
- services/foundry_adapter.py and services/github_adapter.py provide simple, mockable methods for local dev.
- For integration testing, those adapters should be mocked to avoid external network calls.
