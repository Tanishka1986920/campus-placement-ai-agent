from typing import Any, Dict, Optional

from pydantic import BaseModel, constr


class QueryRequest(BaseModel):
    student_id: constr(strip_whitespace=True, min_length=1)
    query: Optional[constr(strip_whitespace=True, min_length=1)] = None
    question: Optional[constr(strip_whitespace=True, min_length=1)] = None


class QueryResponse(BaseModel):
    request_id: str
    result: Dict[str, Any]


class ResumeResponse(BaseModel):
    processing_id: str
    status: str


class StatusResponse(BaseModel):
    id: str
    record: Dict[str, Any]


class UploadResponse(BaseModel):
    processing_id: str
    status: str


class OrchestrationRequest(BaseModel):
    orchestration_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class OrchestrationResponse(BaseModel):
    orchestration_id: Optional[str] = None
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None