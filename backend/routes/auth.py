from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from database import get_db
from models import User
from utils.auth import create_access_token, hash_password, verify_password

router = APIRouter(tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


@router.post("/register")
def register(body: RegisterRequest, db=Depends(get_db)) -> dict[str, Any]:
    existing = db.query(User).filter(User.email == body.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail={"success": False, "error": "Bad Request", "detail": "Email already registered"})

    user = User(email=body.email.lower(), password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return {"success": True, "user_id": user.id}


@router.post("/login")
def login(body: LoginRequest, db=Depends(get_db)) -> dict[str, Any]:
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail={"success": False, "error": "Unauthorized", "detail": "Invalid email or password"})

    token = create_access_token(user_id=user.id)
    return {"success": True, "access_token": token, "token_type": "bearer"}

