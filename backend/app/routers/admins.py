import os
import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_admin, hash_password, verify_password
from ..database import get_db
from ..models import Admin, AdminInviteCode
from ..schemas import (
    AdminLogin,
    AdminRegister,
    AdminResponse,
    InviteCodeCreate,
    InviteCodeListResponse,
    InviteCodeResponse,
    TokenResponse,
)

router = APIRouter(prefix="/api/v1", tags=["admins"])


@router.post("/admins/register", response_model=AdminResponse)
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


@router.post("/admins/login", response_model=TokenResponse)
async def login(admin_data: AdminLogin, db: Annotated[Session, Depends(get_db)]):
    admin = db.query(Admin).filter(Admin.username == admin_data.username).first()
    if not admin or not verify_password(admin_data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(data={"sub": str(admin.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/admins/me", response_model=AdminResponse)
async def get_me(current_admin: Annotated[Admin, Depends(get_current_admin)]):
    return current_admin


@router.post("/admin/invites", response_model=InviteCodeResponse)
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


@router.get("/admin/invites", response_model=InviteCodeListResponse)
async def list_invite_codes(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    codes = db.query(AdminInviteCode).all()
    return InviteCodeListResponse(codes=codes, total=len(codes))


@router.delete("/admin/invites/{code_id}")
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
