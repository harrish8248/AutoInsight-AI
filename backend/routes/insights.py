from __future__ import annotations

import asyncio
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import get_db
from models import AnalysisResult, Dataset
from services import analyzer, insight_generator, visualizer
from utils.auth import CurrentUser

from routes.data import load_dataframe_for_session

router = APIRouter(tags=["insights"])


class SessionRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Dataset session ID returned by /api/upload")


async def _get_or_compute_eda(db, dataset: Dataset, session_id: str) -> dict[str, Any]:
    row = db.query(AnalysisResult).filter(AnalysisResult.dataset_id == dataset.id).first()
    if not row:
        row = AnalysisResult(dataset_id=dataset.id)
        db.add(row)
        db.flush()

    if row.eda_json is not None:
        return row.eda_json

    df: pd.DataFrame
    df = await asyncio.to_thread(pd.read_pickle, dataset.cleaned_path)
    eda = await asyncio.to_thread(analyzer.analyze, df)
    row.eda_json = eda
    db.commit()
    return eda


async def _get_or_compute_insights(db, dataset: Dataset, eda: dict[str, Any]) -> dict[str, Any]:
    row = db.query(AnalysisResult).filter(AnalysisResult.dataset_id == dataset.id).first()
    if not row:
        row = AnalysisResult(dataset_id=dataset.id, eda_json=eda)
        db.add(row)
        db.flush()

    if row.insights_json is not None:
        return row.insights_json

    insights = await asyncio.to_thread(insight_generator.generate_insights, eda)
    row.insights_json = insights
    db.commit()
    return insights


@router.post("/analyze")
async def analyze(
    body: SessionRequest,
    current_user=Depends(CurrentUser),
    db=Depends(get_db),
) -> dict[str, Any]:
    dataset, _df = await load_dataframe_for_session(body.session_id, current_user, db)

    # Ensure EDA + AI analysis are persisted.
    eda = await _get_or_compute_eda(db, dataset, body.session_id)
    ai_analysis = await _get_or_compute_insights(db, dataset, eda)

    return {"success": True, "session_id": body.session_id, "eda": eda, "ai_analysis": ai_analysis}


@router.post("/visualize")
async def visualize(
    body: SessionRequest,
    current_user=Depends(CurrentUser),
    db=Depends(get_db),
) -> dict[str, Any]:
    dataset, df = await load_dataframe_for_session(body.session_id, current_user, db)

    row = db.query(AnalysisResult).filter(AnalysisResult.dataset_id == dataset.id).first()
    if not row:
        row = AnalysisResult(dataset_id=dataset.id)
        db.add(row)
        db.flush()

    if row.charts_json is None:
        charts_payload = await asyncio.to_thread(visualizer.build_visualize_response, df)
        row.charts_json = charts_payload
        db.commit()

    charts = row.charts_json or {}
    return {"success": True, "session_id": body.session_id, **charts}


@router.post("/insights")
async def insights(
    body: SessionRequest,
    current_user=Depends(CurrentUser),
    db=Depends(get_db),
) -> dict[str, Any]:
    dataset, _df = await load_dataframe_for_session(body.session_id, current_user, db)

    eda = await _get_or_compute_eda(db, dataset, body.session_id)
    ai_insights = await _get_or_compute_insights(db, dataset, eda)
    return {"success": True, "session_id": body.session_id, "insights": ai_insights}

