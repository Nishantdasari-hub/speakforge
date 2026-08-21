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

if ENVIRONMENT == "production" and SECRET_KEY == "SUPER_SECRET_DEV_KEY":
    raise RuntimeError("A production SECRET_KEY is required")