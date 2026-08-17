"""Authentication endpoints — register, login, anonymous session."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User, UserRole

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
    # TODO: Check if email already exists
    # TODO: Create user in DB
    # TODO: Return JWT token
    return {
        "access_token": "stub_token",
        "token_type": "bearer",
        "user_id": str(uuid.uuid4()),
        "role": "student",
        "is_anonymous": False,
    }


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    # TODO: Query user, verify password, return JWT
    return {
        "access_token": "stub_token",
        "token_type": "bearer",
        "user_id": str(uuid.uuid4()),
        "role": "student",
        "is_anonymous": False,
    }


@router.post("/anonymous", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def create_anonymous_session(db: AsyncSession = Depends(get_db)):
    """Create an anonymous user session (no email required)."""
    anon_id = uuid.uuid4()
    # TODO: Create anonymous user in DB
    token = create_access_token(data={"sub": str(anon_id), "role": "student", "anon": True})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(anon_id),
        "role": "student",
        "is_anonymous": True,
    }
