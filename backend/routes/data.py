from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from database import get_db
from models import AnalysisResult, Dataset
from utils.auth import CurrentUser
from utils.file_validation import is_allowed_filename
from services import analyzer, file_processor

router = APIRouter(tags=["data"])

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "datasets"
DATA_ROOT.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    current_user=Depends(CurrentUser),
    db=Depends(get_db),
) -> dict[str, Any]:
    if not file.filename or not is_allowed_filename(file.filename):
        raise HTTPException(status_code=400, detail={"success": False, "error": "Bad Request", "detail": "Use CSV or Excel file"})

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail={"success": False, "error": "Bad Request", "detail": "Empty file"})
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail={"success": False, "error": "Payload Too Large", "detail": f"Max upload size is {MAX_UPLOAD_BYTES} bytes"})

    try:
        df = await asyncio.to_thread(file_processor.load_from_bytes, raw, file.filename)
        if df.empty:
            raise HTTPException(status_code=400, detail={"success": False, "error": "Bad Request", "detail": "Dataset has no rows"})

        cleaned = await asyncio.to_thread(file_processor.clean_dataframe, df)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail={"success": False, "error": "Bad Request", "detail": f"Failed to process file: {e}"})

    dataset_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    dataset_dir = DATA_ROOT / dataset_id
    dataset_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = str(dataset_dir / "cleaned.pkl")

    await asyncio.to_thread(cleaned.to_pickle, cleaned_path)

    dataset = Dataset(
        id=dataset_id,
        user_id=current_user.id,
        session_id=session_id,
        filename=file.filename,
        cleaned_path=cleaned_path,
    )
    db.add(dataset)
    db.flush()

    # Pre-create analysis result row so downstream endpoints can update quickly.
    db.add(AnalysisResult(dataset_id=dataset_id))
    db.commit()

    overview = file_processor.dataset_overview(cleaned)
    return {"success": True, "session_id": session_id, "filename": file.filename, **overview}


def _load_df_from_dataset(dataset: Dataset) -> pd.DataFrame:
    return pd.read_pickle(dataset.cleaned_path)


async def load_dataframe_for_session(session_id: str, current_user, db) -> tuple[Dataset, pd.DataFrame]:
    dataset = (
        db.query(Dataset)
        .filter(Dataset.session_id == session_id)
        .filter(Dataset.user_id == current_user.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail={"success": False, "error": "Not Found", "detail": "Unknown dataset session_id"})

    df = await asyncio.to_thread(_load_df_from_dataset, dataset)
    return dataset, df

