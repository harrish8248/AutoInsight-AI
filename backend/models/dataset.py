from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, unique=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    cleaned_path: Mapped[str] = mapped_column(String(1024), nullable=False)  # pickle path
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user = relationship("User", backref="datasets")

    __table_args__ = (UniqueConstraint("session_id", name="uq_datasets_session_id"),)

