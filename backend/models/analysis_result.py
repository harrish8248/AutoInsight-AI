from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, unique=True)

    # EDA JSON
    eda_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # Visualizations JSON
    charts_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # Insights JSON
    insights_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    dataset = relationship("Dataset", backref="analysis_result")

