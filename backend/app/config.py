import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env", encoding="utf-8-sig")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
ALLOWED_ORIGINS = [origin.strip().rstrip("/") for origin in os.getenv(
    "ALLOWED_ORIGINS", FRONTEND_URL
).split(",") if origin.strip()]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
if not UPLOAD_DIR.is_absolute():
    UPLOAD_DIR = PROJECT_ROOT / UPLOAD_DIR
UPLOAD_DIR = UPLOAD_DIR.resolve()

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be configured")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be configured")

if ENVIRONMENT == "production":
    if len(SECRET_KEY) < 32 or SECRET_KEY in {
        "SUPER_SECRET_DEV_KEY", "generate-a-long-random-secret"
    }:
        raise RuntimeError("Set a random production SECRET_KEY of at least 32 characters")
    admin_secret = os.getenv("ADMIN_SECRET_KEY", "")
    if admin_secret and (len(admin_secret) < 32 or admin_secret == "generate-a-separate-admin-secret"):
        raise RuntimeError("Set a random production ADMIN_SECRET_KEY of at least 32 characters")
