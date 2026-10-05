from fastapi import FastAPI
from .database import engine
from . import models
from .routes import auth
from .routes import test
from fastapi.middleware.cors import CORSMiddleware
from app.routes import report
from app.config import ALLOWED_ORIGINS
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter

app = FastAPI(title="SpeakForge API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth")
app.include_router(test.router)   # ✅ FIXED HERE
app.include_router(report.router, prefix="/tests")

@app.get("/health")
def health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "service": "SpeakForge API"
    }
