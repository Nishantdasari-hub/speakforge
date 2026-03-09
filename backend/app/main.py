from fastapi import FastAPI
from .database import engine
from . import models
from .routes import auth
from .routes import test
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Include routers
app.include_router(auth.router, prefix="/auth")
app.include_router(test.router)   # ✅ FIXED HERE

# Create tables
models.Base.metadata.create_all(bind=engine)

# CORS settings
origins = [
    "https://speakforge.com"
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
