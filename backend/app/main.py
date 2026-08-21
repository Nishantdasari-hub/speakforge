import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .database import engine
from . import models
from .routes import auth
from .routes import test

load_dotenv()

app = FastAPI(title="SpeakForge API")

# Include routers
app.include_router(auth.router, prefix="/auth")
app.include_router(test.router)

# Create tables
models.Base.metadata.create_all(bind=engine)

# CORS settings
DEFAULT_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:3000,http://127.0.0.1:3000"
)

origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "SpeakForge API"
    }
