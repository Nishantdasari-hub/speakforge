import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
import jwt
from jwt import InvalidTokenError as JWTError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app import models
from app.services import auth_service
from app.utils.token import create_verification_token, SECRET_KEY, ALGORITHM
from app.utils.email import send_verification_email, send_reset_password_email
from app.config import FRONTEND_URL
from app.email_id import conf
from app.limiter import limiter

router = APIRouter(tags=["Auth"])


class EmailRequest(BaseModel):
    email: EmailStr = Field(max_length=150)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.lower()


def valid_password(value):
    if len(value) < 8 or len(value.encode()) > 72:
        raise ValueError("Use at least 8 characters and at most 72 UTF-8 bytes")
    return value


class RegisterRequest(EmailRequest):
    name: str = Field(min_length=1, max_length=100)
    password: str
    is_admin: bool = False
    admin_key: str | None = None
    _password = field_validator("password")(valid_password)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("Name cannot be blank")
        return value.strip()


class LoginRequest(EmailRequest):
    password: str = Field(min_length=1, max_length=72)

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value):
        if len(value.encode()) > 72:
            raise ValueError("Password exceeds 72 UTF-8 bytes")
        return value


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    new_password: str
    _password = field_validator("new_password")(valid_password)


def require_mail():
    if conf is None:
        raise HTTPException(503, "Email service is unavailable. Please try later.")


@router.post("/register")
@limiter.limit("5/minute")
async def register_user(request: Request, data: RegisterRequest, db: Session = Depends(get_db)):
    require_mail()
    if db.query(models.User).filter_by(email=data.email).first():
        raise HTTPException(400, "Email already registered. Log in or resend verification.")
    if data.is_admin:
        expected = os.getenv("ADMIN_SECRET_KEY", "")
        if not expected or not data.admin_key or not secrets.compare_digest(expected, data.admin_key):
            raise HTTPException(403, "Invalid admin secret key")
    user = models.User(name=data.name, email=data.email, password=auth_service.hash_password(data.password), role="admin" if data.is_admin else "user")
    db.add(user)
    try:
        db.flush()
        await send_verification_email(user.email, create_verification_token(user.email))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(400, "Email already registered") from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(503, "Could not send verification email. Please try registering again.") from exc
    return {"message":"Account created. Check your email to verify before logging in.","role":user.role}


@router.post("/resend-verification")
@limiter.limit("3/minute")
async def resend_verification(request: Request, data: EmailRequest, db: Session = Depends(get_db)):
    require_mail()
    user = db.query(models.User).filter_by(email=data.email, is_verified=False).first()
    if user:
        try:
            await send_verification_email(user.email, create_verification_token(user.email))
        except Exception as exc:
            raise HTTPException(503, "Email service is unavailable. Please try later.") from exc
    return {"message":"If verification is needed, a new link has been sent."}


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"require":["exp"]})
        if payload.get("purpose") != "verify" or not payload.get("email"):
            raise JWTError("Wrong token purpose")
    except JWTError as exc:
        raise HTTPException(400, "Invalid or expired token") from exc
    user = db.query(models.User).filter_by(email=payload["email"]).first()
    if not user:
        raise HTTPException(400, "Invalid or expired token")
    user.is_verified = True
    db.commit()
    return RedirectResponse(f"{FRONTEND_URL}/login")


@router.post("/login")
@limiter.limit("10/minute")
def login_user(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(email=data.email).first()
    if not user or not auth_service.verify_password(data.password, user.password):
        raise HTTPException(400, "Invalid email or password")
    if not user.is_verified:
        raise HTTPException(403, "Please verify your email before logging in.")
    token = auth_service.create_access_token({"sub":user.email,"version":user.token_version})
    return {"access_token":token,"token_type":"bearer","role":user.role,"user_id":user.id}


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: EmailRequest, db: Session = Depends(get_db)):
    require_mail()
    token = auth_service.forgot_password(data.email, db)
    try:
        if token:
            await send_reset_password_email(data.email, f"{FRONTEND_URL}/reset-password/{token}")
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(503, "Email service is unavailable. Please try later.") from exc
    return {"message":"If the email exists, a reset link was sent"}


@router.post("/reset-password")
@limiter.limit("10/minute")
def reset_password(request: Request, data: ResetPasswordRequest, db: Session = Depends(get_db)):
    if not auth_service.reset_password(data.token, data.new_password, db):
        raise HTTPException(400, "Invalid or expired token")
    return {"message":"Password reset successful"}
