"""AutoInsight FastAPI application."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from routes.auth import router as auth_router
from routes.data import upload_dataset as data_upload_dataset
from routes.insights import analyze as insights_analyze, insights as insights_insights, visualize as insights_visualize
from routes.chat import chat as chats_with_dataset, chat_stream as chats_with_dataset_stream
from utils.auth import CurrentUser
from database import Base, engine, get_db

load_dotenv()

app = FastAPI(
    title="AutoInsight API",
    description="Generative AI data analysis backend",
    version="1.0.0",
)

_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
_cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]
if not _cors_origins:
    _cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        status_code = getattr(response, "status_code", 200)
        logging.info("%s %s - %dms (%s)", request.method, request.url.path, duration_ms, status_code)
        return response
    except Exception:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logging.exception("%s %s - %dms", request.method, request.url.path, duration_ms)
        raise

_sessions: dict[str, dict[str, Any]] = {}  # legacy (kept for backward compatibility)


class SessionRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Session ID returned by /api/upload")


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1, max_length=4000)


def _error_payload(message: str, detail: str | None = None) -> dict[str, Any]:
    return {"success": False, "error": message, "detail": detail}


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": "Bad Request",
            "detail": exc.errors(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    status_code = exc.status_code
    # Normalize FastAPI/Starlette HTTPException detail into our structured format.
    detail = exc.detail
    if isinstance(detail, dict):
        error = detail.get("error") or ("Unauthorized" if status_code == 401 else "Bad Request")
        sub_detail = detail.get("detail") if "detail" in detail else detail
        return JSONResponse(status_code=status_code, content={"success": False, "error": error, "detail": sub_detail})

    if status_code == 400:
        error_label = "Bad Request"
    elif status_code == 401:
        error_label = "Unauthorized"
    else:
        error_label = "Server Error" if status_code >= 500 else "Bad Request"
    return JSONResponse(status_code=status_code, content={"success": False, "error": error_label, "detail": detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content=_error_payload("Server Error", "Internal server error"),
    )


app.include_router(auth_router, prefix="/auth")


@app.on_event("startup")
def on_startup():
    # Create tables for quick bootstrap (migrations can be added later).
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
@app.post("/api/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    current_user=Depends(CurrentUser),
    db=Depends(get_db),
):
    # Delegate to DB-backed, JWT-protected implementation.
    return await data_upload_dataset(file=file, current_user=current_user, db=db)


def _get_session(session_id: str) -> dict[str, Any]:
    data = _sessions.get(session_id)
    if not data:
        raise HTTPException(status_code=404, detail=_error_payload("Unknown or expired session_id"))
    return data


@app.post("/analyze")
@app.post("/api/analyze")
async def run_analysis(
    body: SessionRequest,
    current_user=Depends(CurrentUser),
    db=Depends(get_db),
):
    return await insights_analyze(body, current_user=current_user, db=db)


@app.post("/visualize")
@app.post("/api/visualize")
async def run_visualize(
    body: SessionRequest,
    current_user=Depends(CurrentUser),
    db=Depends(get_db),
):
    return await insights_visualize(body, current_user=current_user, db=db)


@app.post("/insights")
@app.post("/api/insights")
async def run_insights(
    body: SessionRequest,
    current_user=Depends(CurrentUser),
    db=Depends(get_db),
):
    return await insights_insights(body, current_user=current_user, db=db)


@app.post("/chat")
@app.post("/api/chat")
async def chat_with_dataset(
    body: ChatRequest,
    current_user=Depends(CurrentUser),
    db=Depends(get_db),
):
    return await chats_with_dataset(body, current_user=current_user, db=db)


@app.post("/chat_stream")
@app.post("/api/chat_stream")
async def chat_with_dataset_stream(
    body: ChatRequest,
    current_user=Depends(CurrentUser),
    db=Depends(get_db),
):
    return await chats_with_dataset_stream(body, current_user=current_user, db=db)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
