import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

from .database import ensure_env_file, get_db, init_db

ensure_env_file()

load_dotenv()

from .models import AppSettings
from .routers import admins_router, employees_router, faces_router, settings_router
from .services.face_service import FaceRecognitionService

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

    db = next(get_db())
    if db.query(AppSettings).first() is None:
        logger.info("Creating default application settings...")
        db.add(AppSettings())
        db.commit()
        logger.info("Default settings created")

    face_service = FaceRecognitionService(model_dir=os.getenv("MODEL_DIR", "models"))
    app.state.face_service = face_service
    logger.info(f"Face recognition: {face_service.model_status}")

    initial_code = os.getenv("INITIAL_INVITE_CODE", "").strip()
    reset_code = os.getenv("RESET_INVITE_CODE", "").strip()
    if initial_code:
        logger.info(f"Initial invite code: {initial_code}")
    else:
        logger.warning("INITIAL_INVITE_CODE not set — registration is closed")
    if reset_code:
        logger.info(f"Reset invite code: {reset_code}")
    else:
        logger.warning("RESET_INVITE_CODE not set — password reset is disabled")

    logger.info("Face Recognition API starting up...")
    yield
    logger.info("Face Recognition API shutting down...")


app = FastAPI(
    title="Face Recognition API",
    description="API for face recognition system with admin authentication",
    version="5.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admins_router)
app.include_router(employees_router)
app.include_router(faces_router)
app.include_router(settings_router)


@app.get("/")
async def root():
    return {"message": "Face Recognition API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "face-recognition-api", "version": "5.0.0"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
