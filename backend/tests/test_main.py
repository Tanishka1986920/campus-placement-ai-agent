import io
import time
import json
from fastapi.testclient import TestClient
from app.main import app, RESUME_STORE

client = TestClient(app)


def test_health_and_openapi_and_correlation():
    # health
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"

    # openapi
    resp = client.get("/api/openapi.json")
    assert resp.status_code == 200
    o = resp.json()
    assert "openapi" in o and o["openapi"].startswith("3")

    # correlation header presence on a simple request
    resp = client.post("/api/query", json={"student_id": "c1", "question": "q"})
    assert resp.status_code == 200
    assert "X-Correlation-ID" in resp.headers


def test_query_rate_limit_and_validation():
    # valid query
    payload = {"student_id": "s1", "question": "How to improve?"}
    resp = client.post("/api/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["student_id"] == "s1"

    # exceed rate limit: perform RATE_LIMIT_MAX requests quickly
    for i in range(0, 10):
        resp = client.post("/api/query", json={"student_id": "rate_test", "question": "q"})
        assert resp.status_code == 200
    # the next should be rejected
    resp = client.post("/api/query", json={"student_id": "rate_test", "question": "q"})
    assert resp.status_code == 429

    # invalid payload
    resp = client.post("/api/query", json={"student": "x"})
    assert resp.status_code == 422


def test_resume_upload_and_processing_flow():
    # create a small fake file
    b = b"Hello resume"
    files = {"file": ("resume.txt", io.BytesIO(b), "text/plain")}
    resp = client.post("/api/resumes", files=files)
    assert resp.status_code == 200
    data = resp.json()
    resume_id = data.get("resume_id")
    assert resume_id

    # initial status should be submitted or processed (background task may finish quickly)
    resp = client.get(f"/api/resumes/{resume_id}/status")
    assert resp.status_code == 200
    s = resp.json()
    assert s["status"] in ("submitted", "processed")

    # wait a short time for background processing to complete (since processing sleeps 1s)
    time.sleep(2)

    # result should be available
    resp = client.get(f"/api/resumes/{resume_id}/result")
    assert resp.status_code == 200
    r = resp.json()
    assert "status" in r
    # If processed, parsed should be present
    if r["status"] == "processed":
        assert isinstance(r.get("parsed"), dict)


def test_resume_upload_errors():
    # empty file
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    resp = client.post("/api/resumes", files=files)
    assert resp.status_code == 400

    # too large file
    big = b"x" * (2 * 1024 * 1024 + 1)
    files = {"file": ("big.bin", io.BytesIO(big), "application/octet-stream")}
    resp = client.post("/api/resumes", files=files)
    assert resp.status_code == 400
