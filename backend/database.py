from __future__ import annotations

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()


class Base(DeclarativeBase):
    pass


def _default_db_path() -> str:
    return os.path.join(os.path.dirname(__file__), "data", "autoinsight.db")


def database_url() -> str:
    return os.getenv("DATABASE_URL", f"sqlite:///{_default_db_path()}").strip()


def make_engine():
    url = database_url()
    if url.startswith("sqlite"):
        # SQLite needs this for access from multiple threads.
        return create_engine(url, connect_args={"check_same_thread": False}, pool_pre_ping=True)
    return create_engine(url, pool_pre_ping=True)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

