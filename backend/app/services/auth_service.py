from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
import os
import secrets
from app.config import SECRET_KEY

# ==============================
# CONFIG
# ==============================

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ==============================
# DATABASE DEPENDENCY
# ==============================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============================
# PASSWORD FUNCTIONS
# ==============================

def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


# ==============================
# JWT TOKEN CREATION
# ==============================

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def generate_reset_token():
    return secrets.token_urlsafe(32)

def token_expiry():
    return datetime.utcnow() + timedelta(minutes=30)


# ==============================
# GET CURRENT USER
# ==============================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()

    if user is None:
        raise credentials_exception

    return user


# ==============================
# ADMIN GUARD
# ==============================

def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return current_user


def forgot_password(email, db):

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        return None

    token = generate_reset_token()

    user.reset_token = token
    user.reset_token_expiry = token_expiry()

    db.commit()

    return token

def reset_password(token, new_password, db):

    user = db.query(models.User).filter(models.User.reset_token == token).first()

    if not user:
        return False

    if user.reset_token_expiry < datetime.utcnow():
        return False

    user.password = hash_password(new_password)

    user.reset_token = None
    user.reset_token_expiry = None

    db.commit()

    return True