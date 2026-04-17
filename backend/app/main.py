import os
import secrets
import shutil
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Annotated

import cv2
import numpy as np
import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

load_dotenv()

from .auth import create_access_token, get_current_admin, hash_password, verify_password
from .database import ensure_env_file, get_db, init_db
from .models import Admin, AdminInviteCode, AppSettings, Employee
from .schemas import (
    AdminLogin,
    AdminRegister,
    AdminResponse,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeStats,
    EmployeeUpdate,
    InviteCodeCreate,
    InviteCodeListResponse,
    InviteCodeResponse,
    SettingsResponse,
    SettingsUpdate,
    TokenResponse,
)
from .services.face_service import FaceRecognitionService

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

face_service = FaceRecognitionService(model_dir=os.getenv("MODEL_DIR", "models"))


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
    version="4.0.0",
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


def decode_image(contents: bytes) -> np.ndarray:
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    return img


@app.get("/")
async def root():
    return {"message": "Face Recognition API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "face-recognition-api", "version": "4.0.0"}


@app.post("/api/v1/admins/register", response_model=AdminResponse)
async def register_admin(
    admin_data: AdminRegister, db: Annotated[Session, Depends(get_db)]
):
    existing = (
        db.query(Admin)
        .filter(
            (Admin.username == admin_data.username) | (Admin.email == admin_data.email)
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Username or email already registered"
        )

    initial_invite_code = os.getenv("INITIAL_INVITE_CODE", "").strip()

    if not initial_invite_code:
        raise HTTPException(
            status_code=403, detail="Registration is closed. Contact administrator."
        )

    if admin_data.invite_code != initial_invite_code:
        raise HTTPException(status_code=403, detail="Invalid invite code")

    new_admin = Admin(
        username=admin_data.username,
        email=admin_data.email,
        password_hash=hash_password(admin_data.password),
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return new_admin


@app.post("/api/v1/admins/login", response_model=TokenResponse)
async def login(admin_data: AdminLogin, db: Annotated[Session, Depends(get_db)]):
    admin = db.query(Admin).filter(Admin.username == admin_data.username).first()
    if not admin or not verify_password(admin_data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(data={"sub": str(admin.id)})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/v1/admins/me", response_model=AdminResponse)
async def get_me(current_admin: Annotated[Admin, Depends(get_current_admin)]):
    return current_admin


@app.post("/api/v1/admin/invites", response_model=InviteCodeResponse)
async def create_invite_code(
    invite_data: InviteCodeCreate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    code = secrets.token_urlsafe(16)[:16]
    expires_at = datetime.utcnow() + timedelta(hours=invite_data.expires_hours)

    invite_code = AdminInviteCode(
        code=code,
        created_by=current_admin.id,
        expires_at=expires_at,
    )
    db.add(invite_code)
    db.commit()
    db.refresh(invite_code)
    return invite_code


@app.get("/api/v1/admin/invites", response_model=InviteCodeListResponse)
async def list_invite_codes(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    codes = db.query(AdminInviteCode).all()
    return InviteCodeListResponse(codes=codes, total=len(codes))


@app.delete("/api/v1/admin/invites/{code_id}")
async def delete_invite_code(
    code_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    invite_code = (
        db.query(AdminInviteCode).filter(AdminInviteCode.id == code_id).first()
    )
    if not invite_code:
        raise HTTPException(status_code=404, detail="Invite code not found")

    if invite_code.is_used:
        raise HTTPException(status_code=400, detail="Cannot delete used invite code")

    db.delete(invite_code)
    db.commit()
    return {"message": f"Invite code {code_id} deleted successfully"}


@app.post("/api/v1/employees/register", response_model=EmployeeResponse)
async def register_employee(
    username: str = Form(...),
    employee_id: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    department: str = Form(""),
    position: str = Form(""),
    location: str = Form(""),
    hire_date: str = Form(""),
    is_active: bool = Form(True),
    access_enabled: bool = Form(True),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    if employee_id:
        existing_employee_id = (
            db.query(Employee).filter(Employee.employee_id == employee_id).first()
        )
        if existing_employee_id:
            raise HTTPException(
                status_code=400,
                detail="Employee with this employee_id already exists",
            )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Maximum size: {MAX_IMAGE_SIZE // (1024 * 1024)}MB",
        )

    try:
        img = decode_image(contents)
    except HTTPException:
        raise

    try:
        faces = face_service.detect_faces(img)

        if len(faces) == 0:
            raise HTTPException(status_code=400, detail="No face detected in the image")

        if len(faces) > 1:
            raise HTTPException(
                status_code=400,
                detail="Multiple faces detected. Please provide an image with a single face.",
            )

        x, y, w, h = faces[0]
        face_img = img[y : y + h, x : x + w]

        embedding = face_service.get_face_embedding(face_img)

        if embedding is None:
            raise HTTPException(
                status_code=500, detail="Failed to extract face embedding"
            )

        employee = Employee(
            employee_id=employee_id,
            username=username,
            email=email,
            phone=phone,
            department=department,
            position=position,
            location=location,
            hire_date=hire_date,
            is_active=is_active,
            access_enabled=access_enabled,
            embedding=embedding.tobytes(),
        )

        db.add(employee)
        db.commit()
        db.refresh(employee)

        return employee

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/employees", response_model=list[EmployeeResponse])
async def list_employees(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
    skip: int = 0,
    limit: int = 100,
):
    employees = db.query(Employee).offset(skip).limit(limit).all()
    return employees


@app.get("/api/v1/employees/search", response_model=list[EmployeeResponse])
async def search_employees(
    q: str,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    pattern = f"%{q}%"
    employees = (
        db.query(Employee)
        .filter(
            Employee.username.ilike(pattern)
            | Employee.position.ilike(pattern)
            | Employee.department.ilike(pattern)
            | Employee.email.ilike(pattern)
        )
        .all()
    )
    return employees


@app.get("/api/v1/employees/stats", response_model=EmployeeStats)
async def get_employee_stats(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    total = db.query(Employee).count()
    active = db.query(Employee).filter(Employee.is_active == True).count()
    inactive = total - active
    return EmployeeStats(total=total, active=active, inactive=inactive)


@app.put("/api/v1/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    update_data: EmployeeUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(employee, key, value)

    db.commit()
    db.refresh(employee)
    return employee


@app.delete("/api/v1/employees/{employee_id}")
async def delete_employee(
    employee_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(employee)
    db.commit()

    return {"message": f"Employee {employee_id} deleted successfully"}


@app.post("/api/v1/faces/recognize")
async def recognize_file(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Maximum size: {MAX_IMAGE_SIZE // (1024 * 1024)}MB",
        )

    try:
        img = decode_image(contents)
    except HTTPException:
        raise

    try:
        faces = face_service.detect_faces(img)

        if len(faces) == 0:
            return {
                "faces_detected": 0,
                "results": [],
                "message": "No faces detected in the image",
            }

        known_faces = db.query(Employee).all()

        known_embeddings = np.array(
            [
                np.frombuffer(record.embedding, dtype=np.float64)
                for record in known_faces
            ]
        )
        known_records = known_faces

        results = []

        for x, y, w, h in faces:
            face_img = img[y : y + h, x : x + w]
            embedding = face_service.get_face_embedding(face_img)

            if embedding is None:
                continue

            similarities = face_service.compare_faces_batch(embedding, known_embeddings)

            matches = []
            for i, similarity in enumerate(similarities):
                if similarity > 0.4:
                    record = known_records[i]
                    matches.append(
                        {
                            "id": record.id,
                            "username": record.username,
                            "position": record.position or "",
                            "department": record.department or "",
                            "email": record.email or "",
                            "phone": record.phone or "",
                            "location": record.location or "",
                            "hire_date": record.hire_date or "",
                            "is_active": record.is_active,
                            "access_enabled": record.access_enabled,
                            "similarity": float(similarity),
                        }
                    )

            matches.sort(key=lambda m: m["similarity"], reverse=True)
            results.append({"bbox": [x, y, w, h], "matches": matches})

        return {
            "faces_detected": len(faces),
            "results": results,
            "message": f"Processed {len(faces)} face(s)",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/settings", response_model=SettingsResponse)
async def get_settings(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    settings = db.query(AppSettings).first()
    if settings is None:
        settings = AppSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@app.put("/api/v1/settings", response_model=SettingsResponse)
async def update_settings(
    update_data: SettingsUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    settings = db.query(AppSettings).first()
    if settings is None:
        settings = AppSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(settings, key, value)

    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    return settings


@app.post("/api/v1/settings/backup")
async def create_backup(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    try:
        db_path = "data/faces.db"
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="Database file not found")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"data/backup_faces_{timestamp}.db"
        shutil.copy2(db_path, backup_path)

        return {
            "message": "Backup created successfully",
            "backup_path": backup_path,
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create backup")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
