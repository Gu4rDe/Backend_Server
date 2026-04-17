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

load_dotenv()

from .database import ensure_env_file, get_db, init_db
from .models import AppSettings
from .routers import admins_router, employees_router, faces_router, settings_router

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_env_file()
    init_db()
    db = next(get_db())
    if db.query(AppSettings).first() is None:
        db.add(AppSettings())
        db.commit()
    print("Face Recognition API starting up...")
    yield
    print("Face Recognition API shutting down...")


app = FastAPI(
    title="Face Recognition API",
    description="API for face recognition system with admin authentication",
    version="4.1.0",
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
    return {"status": "healthy", "service": "face-recognition-api", "version": "4.1.0"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
