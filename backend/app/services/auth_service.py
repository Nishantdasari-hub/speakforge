from datetime import datetime, timedelta
import hashlib
import secrets

import jwt
from jwt import InvalidTokenError as JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.config import SECRET_KEY

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(password, hashed):
    return pwd_context.verify(password, hashed)


def create_access_token(data):
    payload = dict(data, exp=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), purpose="access")
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    error = HTTPException(401, "Could not validate credentials", headers={"WWW-Authenticate":"Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"require":["exp"]})
        if payload.get("purpose") != "access" or not payload.get("sub"):
            raise error
    except JWTError as exc:
        raise error from exc
    user = db.query(models.User).filter_by(email=payload["sub"]).first()
    if not user or not user.is_verified or payload.get("version") != user.token_version:
        raise error
    return user


def get_current_admin(user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Admin privileges required")
    return user


def generate_reset_token():
    return secrets.token_urlsafe(32)


def token_expiry():
    return datetime.utcnow() + timedelta(minutes=30)


def digest_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def forgot_password(email, db):
    user = db.query(models.User).filter_by(email=email, is_verified=True).with_for_update().first()
    if not user:
        return None
    token = generate_reset_token()
    user.reset_token, user.reset_token_expiry = digest_token(token), token_expiry()
    db.flush()
    return token


def reset_password(token, new_password, db):
    user = db.query(models.User).filter_by(reset_token=digest_token(token)).with_for_update().first()
    if not user or not user.reset_token_expiry or user.reset_token_expiry <= datetime.utcnow():
        return False
    user.password = hash_password(new_password)
    user.reset_token = user.reset_token_expiry = None
    user.token_version += 1
    db.commit()
    return True
