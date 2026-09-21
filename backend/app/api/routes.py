import uuid
import os
import tempfile
from typing import Dict, Any

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    BackgroundTasks,
    Request,
)
from fastapi.responses import JSONResponse

from app.foundry_client import FoundryClient
from app.schemas import QueryRequest

foundry_client = FoundryClient()

router = APIRouter()

# Simple in-memory stores for results and resume processing status
RESULT_STORE: Dict[str, Dict[str, Any]] = {}
RESUME_STORE: Dict[str, Dict[str, Any]] = {}

# Simple per-student query rate limiter
QUERY_REQUEST_COUNT: Dict[str, int] = {}
RATE_LIMIT_MAX = 10


# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@router.get("/health")
async def health_check():
    return {"status": "ok"}


# --------------------------------------------------
# STUDENT QUERY
# --------------------------------------------------

@router.post("/query")
async def student_query(payload: QueryRequest):

    student_id = payload.student_id
    query_text = payload.query or payload.question

    if not query_text:
        raise HTTPException(
            status_code=422,
            detail="query or question is required",
        )

    if not student_id:
        raise HTTPException(
            status_code=422,
            detail="student_id is required",
        )

    if not query_text:
        raise HTTPException(
            status_code=422,
            detail="query or question is required",
        )

    # Rate limit: one student can make maximum 10 requests
    current_count = QUERY_REQUEST_COUNT.get(student_id, 0)

    if current_count >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
        )

    QUERY_REQUEST_COUNT[student_id] = current_count + 1

    query_id = str(uuid.uuid4())

    foundry_result = await foundry_client.process_query({
    "student_id": student_id,
    "query": query_text,
})

    result = {
        "echo": {
            "student_id": student_id,
            "query": query_text,
        },
        "answer": foundry_result.get(
            "recommendation",
            f"Received query: {query_text}",
        ),
        "foundry_result": foundry_result,
        "metadata": {
            "source": "microsoft-foundry"
        },
    }

    RESULT_STORE[query_id] = {
        "id": query_id,
        "type": "query",
        "student_id": student_id,
        "result": result,
    }

    return {
        "request_id": query_id,
        "student_id": student_id,
        "question": query_text,
        "query": query_text,
        "answer": result["answer"],
        "result": result,
    }


# --------------------------------------------------
# RESUME HELPERS
# --------------------------------------------------

def _validate_file_type(filename: str) -> bool:

    allowed = {
        "pdf",
        "doc",
        "docx",
        "txt",
    }

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1,
    )[-1].lower()

    return extension in allowed


async def _process_resume_file(
    resume_id: str,
    filepath: str,
):

    try:
        foundry_resume_result = await foundry_client.process_resume(
            filepath
        )

        with open(filepath, "rb") as file:
            data = file.read()

        size = len(data)

        try:
            text = data.decode("utf-8")[:2000]
        except Exception:
            text = "(binary content)"

        parsed = {
            "filename": RESUME_STORE[
                resume_id
            ].get("filename"),
            "size_bytes": size,
            "text_preview": text[:500],
            "foundry_result": foundry_resume_result,
        }

        RESUME_STORE[resume_id][
            "status"
        ] = "processed"

        RESUME_STORE[resume_id][
            "parsed"
        ] = parsed

        RESUME_STORE[resume_id][
            "result"
        ] = {
            "resume_id": resume_id,
            "status": "processed",
            "parsed": parsed,
        }

        RESUME_STORE[resume_id][
            "record"
        ] = {
            "id": resume_id,
            "type": "resume",
            "status": "processed",
            "parsed": parsed,
        }

    except Exception as exc:

        RESUME_STORE[resume_id][
            "status"
        ] = "failed"

        RESUME_STORE[resume_id][
            "error"
        ] = str(exc)

    finally:

        try:
            os.remove(filepath)
        except Exception:
            pass


# --------------------------------------------------
# RESUME UPLOAD
# --------------------------------------------------

async def _upload_resume_common(
    background_tasks: BackgroundTasks,
    file: UploadFile,
):

    filename = file.filename or "upload"

    if not _validate_file_type(filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded",
        )

    resume_id = str(uuid.uuid4())

    tmp_path = os.path.join(
        tempfile.gettempdir(),
        f"resume_{resume_id}",
    )

    with open(tmp_path, "wb") as output_file:
        output_file.write(contents)

    try:
        await file.close()
    except Exception:
        pass

    RESUME_STORE[resume_id] = {
        "status": "submitted",
        "filename": filename,
    }

    background_tasks.add_task(
        _process_resume_file,
        resume_id,
        tmp_path,
    )

    return {
        "resume_id": resume_id,
        "processing_id": resume_id,
        "status": "submitted",
        "filename": filename,
    }


# Singular endpoint - compatibility
@router.post("/resume")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    return await _upload_resume_common(
        background_tasks,
        file,
    )


# Plural endpoint - required by tests
@router.post("/resumes")
async def upload_resumes(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    return await _upload_resume_common(
        background_tasks,
        file,
    )


# --------------------------------------------------
# RESUME STATUS
# --------------------------------------------------

@router.get("/resumes/{resume_id}/status")
async def resume_status(resume_id: str):

    if resume_id not in RESUME_STORE:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    entry = RESUME_STORE[resume_id]

    return {
        "resume_id": resume_id,
        "status": entry.get(
            "status",
            "submitted",
        ),
    }


# --------------------------------------------------
# RESUME RESULT
# --------------------------------------------------

@router.get("/resumes/{resume_id}/result")
async def resume_result(resume_id: str):

    if resume_id not in RESUME_STORE:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    entry = RESUME_STORE[resume_id]

    status = entry.get(
        "status",
        "submitted",
    )

    if status != "processed":
        return {
            "resume_id": resume_id,
            "status": status,
        }

    return entry.get(
        "result",
        {
            "resume_id": resume_id,
            "status": "processed",
            "parsed": entry.get(
                "parsed",
                {},
            ),
        },
    )


# --------------------------------------------------
# GENERIC STATUS
# --------------------------------------------------

@router.get("/status/{item_id}")
async def get_status(item_id: str):

    if item_id in RESUME_STORE:

        entry = RESUME_STORE[item_id]

        record = entry.get(
            "record"
        ) or {
            "id": item_id,
            "type": "resume",
            "status": entry.get(
                "status",
                "submitted",
            ),
        }

        return {
            "id": item_id,
            "record": record,
        }

    if item_id in RESULT_STORE:

        return {
            "id": item_id,
            "record": {
                "id": item_id,
                "type": "query",
                "status": "completed",
            },
        }

    raise HTTPException(
        status_code=404,
        detail="Item not found",
    )


# --------------------------------------------------
# GENERIC RESULTS
# --------------------------------------------------

@router.get("/results/{item_id}")
async def get_results(item_id: str):

    if item_id in RESUME_STORE:

        entry = RESUME_STORE[item_id]

        return {
            "id": item_id,
            "status": entry.get(
                "status"
            ),
            "record": entry.get(
                "record",
                {},
            ),
        }

    if item_id in RESULT_STORE:

        return {
            "id": item_id,
            "status": "completed",
            "result": RESULT_STORE[
                item_id
            ].get("result", {}),
        }

    raise HTTPException(
        status_code=404,
        detail="Item not found",
    )