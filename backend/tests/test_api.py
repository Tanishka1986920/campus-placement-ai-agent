import os
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_query_endpoint():
    payload = {"student_id": "stu123", "query": "What internships are available?"}
    r = client.post("/api/query", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "request_id" in data
    assert "result" in data
    assert data["result"]["echo"]["student_id"] == "stu123"

def test_resume_upload_and_status():
    # Create a small sample file
    sample = io.BytesIO(b"John Doe\nExperience: None\n")
    files = {"file": ("sample_resume.txt", sample, "text/plain")}
    r = client.post("/api/resume", files=files)
    assert r.status_code == 200
    data = r.json()
    pid = data.get("processing_id")
    assert pid
    # Immediately check status (may still be processing or done)
    r2 = client.get(f"/api/status/{pid}")
    assert r2.status_code == 200
    rec = r2.json().get("record")
    assert rec.get("type") == "resume"

def test_bad_resume_type():
    sample = io.BytesIO(b"not a valid resume")
    files = {"file": ("sample_resume.exe", sample, "application/octet-stream")}
    r = client.post("/api/resume", files=files)
    assert r.status_code == 400
