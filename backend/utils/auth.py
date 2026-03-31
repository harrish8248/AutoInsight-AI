from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from database import get_db
from models import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    import bcrypt

    if password is None:
        raise ValueError("Password cannot be empty")

    rounds = int(os.getenv("BCRYPT_ROUNDS", "12"))
    salt = bcrypt.gensalt(rounds=rounds)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    import bcrypt

    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "dev-please-change-me").strip()


def create_access_token(*, user_id: str, expires_minutes: int = 60 * 24 * 7) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)
    payload = {"sub": user_id, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, jwt_secret(), algorithm=os.getenv("ALGORITHM", "HS256"))


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"success": False, "error": "Unauthorized", "detail": "Invalid or missing token."},
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, jwt_secret(), algorithms=[os.getenv("ALGORITHM", "HS256")])
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_id(db, user_id)
    if not user:
        raise credentials_exception
    return user


CurrentUser = get_current_user

