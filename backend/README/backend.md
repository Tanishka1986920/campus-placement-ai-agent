Campus Placement Backend

This backend implements a FastAPI application with endpoints required by the Campus Placement AI project.

Environment variables
- ALLOWED_ORIGINS: comma-separated list of allowed CORS origins (default: http://localhost:3000)
- TMP_DIR: directory to store uploaded files temporarily (default: /tmp)
- FOUNDRY_ENDPOINT: optional (not required for stub mode)
- FOUNDRY_API_KEY: optional (not required for stub mode)

Endpoints
- GET /health
  - Returns {"status":"ok"}

- POST /api/query
  - Accepts JSON body: {"student_id": "...", "query": "..."}
  - Returns {"request_id": "...", "result": {...}}

- POST /api/resume
  - Accepts multipart/form-data with file field named "file"
  - Returns {"processing_id": "...", "status": "processing"}
  - Processing is done in background; query /api/status/{id} to get results

- GET /api/status/{id}
  - Returns current record for the given id

- GET /api/results/{id}
  - Returns stored result for the id

Testing
- The tests use FastAPI TestClient. To run tests:
  - pip install -r requirements.txt (see project root requirements)
  - pytest

Manual testing (curl)
- Health: curl http://localhost:8000/health
- Query: curl -X POST http://localhost:8000/api/query -H "Content-Type: application/json" -d '{"student_id":"s1","query":"skills"}'
- Resume: curl -F "file=@sample_resume.txt" http://localhost:8000/api/resume

Notes
- Foundry integration is stubbed; implement real calls in app/foundry_client.py when credentials are available.
