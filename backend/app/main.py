import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .database import ensure_env_file, get_db, init_db
from .models import AppSettings
from .routers import admins_router, employees_router, faces_router, settings_router


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
