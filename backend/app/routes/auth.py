import os
import secrets
from jose import jwt, JWTError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.services.auth_service import hash_password, verify_password, create_access_token
from pydantic import BaseModel
from dotenv import load_dotenv
from app.utils.token import SECRET_KEY, ALGORITHM, create_verification_token
from app.utils.email import send_verification_email
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from app.services import auth_service
from app.utils.email import send_verification_email, send_reset_password_email
from app.config import FRONTEND_URL

load_dotenv()

router = APIRouter(
    prefix="",
    tags=["Auth"]
)


# ---------------- REQUEST MODELS ---------------- #

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    is_admin: bool = False
    admin_key: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


# ---------------- REGISTER ---------------- #

@router.post("/register")

async def register_user(request: RegisterRequest, db: Session = Depends(get_db)):

    existing_user = db.query(models.User)\
        .filter(models.User.email == request.email)\
        .first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    role = "user"

    # Admin registration validation
    if request.is_admin:
        env_key = os.getenv("ADMIN_SECRET_KEY")

        if not request.admin_key or request.admin_key != env_key:
            raise HTTPException(status_code=403, detail="Invalid admin secret key")

        role = "admin"

    new_user = models.User(
        name=request.name,
        email=request.email,
        password=hash_password(request.password),
        role=role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_verification_token(new_user.email)

    await send_verification_email(new_user.email, token)

    return {
        "message": "User registered successfully",
        "role": role
    }

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):

    print("TOKEN RECEIVED:", token)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("PAYLOAD:", payload)

        email = payload.get("email")
        print("EMAIL:", email)

    except JWTError as e:
        print("JWT ERROR:", e)
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.email == email).first()
    print("USER FOUND:", user)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.commit()

    return RedirectResponse(url=f"{FRONTEND_URL}/login")
# ---------------- LOGIN ---------------- #

@router.post("/login")
def login_user(request: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(models.User)\
        .filter(models.User.email == request.email)\
        .first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in.")

    if not verify_password(request.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token = create_access_token(
        data={"sub": user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }

class ForgotPasswordRequest(BaseModel):
    email: str

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):

    token = auth_service.forgot_password(data.email, db)

    if token:
        reset_link = f"{FRONTEND_URL}/reset-password/{token}"
        await send_reset_password_email(data.email, reset_link)

    return {"message": "If the email exists, a reset link was sent"}

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):

    success = auth_service.reset_password(data.token, data.new_password, db)

    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    return {"message": "Password reset successful"}