"""Authentication endpoints — register, login, anonymous session."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    year_of_study: Optional[int] = None
    major: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    is_anonymous: bool


# ── Endpoints ─────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new student account."""
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        role="student",
        is_anonymous=False,
        full_name=data.full_name,
        year_of_study=data.year_of_study,
        major=data.major,
    )
    db.add(user)
    await db.flush()

    token = create_access_token(data={"sub": str(user.id), "role": "student"})
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        role="student",
        is_anonymous=False,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        role=user.role,
        is_anonymous=False,
    )


@router.post("/anonymous", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def create_anonymous_session(db: AsyncSession = Depends(get_db)):
    """Create an anonymous user session (no email required)."""
    user = User(
        role="student",
        is_anonymous=True,
    )
    db.add(user)
    await db.flush()

    token = create_access_token(data={"sub": str(user.id), "role": "student", "anon": True})
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        role="student",
        is_anonymous=True,
    )

