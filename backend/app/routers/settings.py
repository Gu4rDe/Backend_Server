import os
import shutil
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_admin
from ..database import get_db
from ..models import Admin, AppSettings
from ..schemas import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/v1", tags=["settings"])


@router.get("/settings", response_model=SettingsResponse)
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


@router.put("/settings", response_model=SettingsResponse)
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

    settings.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(settings)
    return settings


@router.post("/settings/backup")
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
