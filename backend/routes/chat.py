from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Generator

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models import AnalysisResult, ChatMessage, Dataset
from services import analyzer, chat_service
from services.vector_store import vector_store
from utils.auth import CurrentUser

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1, max_length=4000)


def _get_dataset_by_session(db: Session, *, session_id: str, user_id: str) -> Dataset | None:
    return db.query(Dataset).filter(Dataset.session_id == session_id, Dataset.user_id == user_id).first()


async def _get_or_compute_eda_json(db: Session, dataset: Dataset) -> dict[str, Any]:
    row = db.query(AnalysisResult).filter(AnalysisResult.dataset_id == dataset.id).first()
    if row and row.eda_json is not None:
        return row.eda_json

    df = await asyncio.to_thread(pd.read_pickle, dataset.cleaned_path)
    eda = await asyncio.to_thread(analyzer.analyze, df)

    if not row:
        row = AnalysisResult(dataset_id=dataset.id)
        db.add(row)
        db.flush()

    row.eda_json = eda
    db.commit()
    return eda


@router.post("/chat")
async def chat(
    body: ChatRequest,
    current_user=Depends(CurrentUser),
    db=Depends(get_db),
) -> dict[str, Any]:
    dataset = _get_dataset_by_session(db, session_id=body.session_id, user_id=current_user.id)
    if not dataset:
        raise HTTPException(status_code=404, detail={"success": False, "error": "Not Found", "detail": "Unknown dataset session_id"})

    eda = await _get_or_compute_eda_json(db, dataset)

    # Build index if needed (in-memory); rebuilt after restart.
    await asyncio.to_thread(vector_store.ensure_built, body.session_id, eda)
    retrieved = vector_store.query(body.session_id, body.question, top_k=5)
    retrieved_docs = [x["doc"] for x in retrieved if x.get("doc")]

    result = await asyncio.to_thread(
        chat_service.chat_with_data,
        eda,
        body.question,
        retrieved_context=retrieved_docs,
    )

    user_msg = ChatMessage(
        dataset_id=dataset.id,
        user_id=current_user.id,
        role="user",
        question_text=body.question,
        answer_text=None,
        confidence=None,
    )
    assistant_msg = ChatMessage(
        dataset_id=dataset.id,
        user_id=current_user.id,
        role="assistant",
        question_text=None,
        answer_text=result.get("answer"),
        confidence=result.get("confidence"),
    )
    db.add(user_msg)
    db.add(assistant_msg)
    db.commit()

    return {
        "success": True,
        "session_id": body.session_id,
        "answer": result.get("answer"),
        "confidence": result.get("confidence"),
    }


@router.post("/chat_stream")
async def chat_stream(
    body: ChatRequest,
    current_user=Depends(CurrentUser),
    db=Depends(get_db),
) -> StreamingResponse:
    dataset = _get_dataset_by_session(db, session_id=body.session_id, user_id=current_user.id)
    if not dataset:
        raise HTTPException(status_code=404, detail={"success": False, "error": "Not Found", "detail": "Unknown dataset session_id"})

    dataset_id = dataset.id
    current_user_id = current_user.id
    question_text = body.question
    eda = await _get_or_compute_eda_json(db, dataset)
    await asyncio.to_thread(vector_store.ensure_built, body.session_id, eda)
    retrieved = vector_store.query(body.session_id, body.question, top_k=5)
    retrieved_docs = [x["doc"] for x in retrieved if x.get("doc")]

    inner_gen = chat_service.chat_stream_with_data(eda, question_text, retrieved_context=retrieved_docs)

    answer_parts: list[str] = []
    final_answer: str | None = None
    final_conf: str | None = None

    def _iter() -> Generator[bytes, None, None]:
        nonlocal final_answer, final_conf
        try:
            for chunk in inner_gen:
                # chunk is NDJSON string with newline; stream it through.
                yield chunk.encode("utf-8") if isinstance(chunk, str) else chunk

                # Capture assistant answer for persistence.
                try:
                    obj = json.loads(chunk.strip())
                except Exception:
                    continue
                t = obj.get("type")
                if t == "token":
                    tok = obj.get("token")
                    if tok:
                        answer_parts.append(str(tok))
                elif t == "final":
                    final_answer = obj.get("answer", None)
                    final_conf = obj.get("confidence", None)
        finally:
            # Persist chat messages after the stream completes.
            try:
                assistant_text = final_answer if final_answer is not None else "".join(answer_parts).strip()
                if assistant_text:
                    db2 = SessionLocal()
                    try:
                        user_msg = ChatMessage(
                            dataset_id=dataset_id,
                            user_id=current_user_id,
                        role="user",
                        question_text=question_text,
                        answer_text=None,
                        confidence=None,
                        )
                        assistant_msg = ChatMessage(
                            dataset_id=dataset_id,
                            user_id=current_user_id,
                        role="assistant",
                        question_text=None,
                        answer_text=assistant_text,
                        confidence=final_conf,
                        )
                        db2.add(user_msg)
                        db2.add(assistant_msg)
                        db2.commit()
                    finally:
                        db2.close()
            except Exception:
                # Persistence failures should not break the streaming response.
                pass

    return StreamingResponse(_iter(), media_type="application/x-ndjson")

