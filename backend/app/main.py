import os
import uuid
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import router as api_router, RESULT_STORE, RESUME_STORE


LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("backend")


app = FastAPI(
    title="Campus Placement AI - Backend",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

allowed = os.environ.get("ALLOWED_ORIGINS", "*")

if allowed.strip() == "*":
    origins = ["*"]
else:
    origins = [
        origin.strip()
        for origin in allowed.split(",")
        if origin.strip()
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# --------------------------------------------------
# CORRELATION ID MIDDLEWARE
# --------------------------------------------------

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):

    correlation_id = request.headers.get(
        "X-Correlation-ID"
    ) or str(uuid.uuid4())

    request.state.correlation_id = correlation_id

    response = await call_next(request)

    response.headers["X-Correlation-ID"] = correlation_id

    return response


# --------------------------------------------------
# API ROUTER
# --------------------------------------------------

app.include_router(
    api_router,
    prefix="/api"
)


# --------------------------------------------------
# BASIC ROUTES
# --------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Campus Placement AI Backend"
    }


@app.get("/health")
async def root_health():
    return {
        "status": "ok"
    }


# --------------------------------------------------
# EXCEPTION HANDLERS
# --------------------------------------------------

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request,
    exc: Exception
):

    logger.exception(
        "Unhandled exception: %s",
        exc
    )

    message = (
        str(exc)
        if os.environ.get("DEBUG") == "1"
        else "An internal error occurred."
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": message,
        },
    )


# --------------------------------------------------
# APPLICATION EVENTS
# --------------------------------------------------

@app.on_event("startup")
async def startup_event():
    logger.info(
        "Starting backend application"
    )


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(
        "Shutting down backend application"
    )