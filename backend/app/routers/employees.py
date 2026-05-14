from typing import Annotated

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..auth import get_current_admin
from ..database import get_db
from ..deps import get_face_service
from ..models import Admin, Employee
from ..schemas import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeStats,
    EmployeeUpdate,
)
from ..services.embedding import serialize_embedding
from ..services.face_service import FaceRecognitionService

router = APIRouter(prefix="/api/v1", tags=["employees"])

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


def decode_image(contents: bytes) -> np.ndarray:
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    return img


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize and truncate string input."""
    if not value:
        return ""
    # Remove leading/trailing whitespace and truncate
    return value.strip()[:max_length]


@router.post("/employees/register", response_model=EmployeeResponse)
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
    face_service: FaceRecognitionService = Depends(get_face_service),
):
    # Sanitize inputs
    username = sanitize_string(username, 150)
    employee_id = sanitize_string(employee_id, 50)
    email = sanitize_string(email, 100).lower()
    phone = sanitize_string(phone, 30)
    department = sanitize_string(department, 100)
    position = sanitize_string(position, 100)
    location = sanitize_string(location, 100)
    hire_date = sanitize_string(hire_date, 20)
    
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
        face_results = face_service.detect_and_embed(img)

        if len(face_results) == 0:
            raise HTTPException(status_code=400, detail="No face detected in the image")

        if len(face_results) > 1:
            raise HTTPException(
                status_code=400,
                detail="Multiple faces detected. Please provide an image with a single face.",
            )

        face = face_results[0]

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
            embedding=serialize_embedding(face.embedding),
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


@router.get("/employees", response_model=list[EmployeeResponse])
async def list_employees(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
    skip: int = 0,
    limit: int = 100,
):
    employees = db.query(Employee).offset(skip).limit(limit).all()
    return employees


@router.get("/employees/search", response_model=list[EmployeeResponse])
async def search_employees(
    q: str,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    # Sanitize search query
    q = sanitize_string(q, 100)
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


@router.get("/employees/stats", response_model=EmployeeStats)
async def get_employee_stats(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    total = db.query(Employee).count()
    active = db.query(Employee).filter(Employee.is_active == True).count()
    inactive = total - active
    return EmployeeStats(total=total, active=active, inactive=inactive)


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
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


@router.delete("/employees/{employee_id}")
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
