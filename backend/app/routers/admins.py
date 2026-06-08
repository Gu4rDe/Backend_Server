import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_admin, hash_password, verify_password
from ..database import get_db
from ..models import Admin, AdminInviteCode
from ..services.invite_service import InviteService
from ..schemas import (
    AdminLogin,
    AdminPasswordReset,
    AdminRegister,
    AdminResponse,
    InviteCodeCreate,
    InviteCodeListResponse,
    InviteCodeResponse,
    MessageResponse,
    TokenResponse,
)

router = APIRouter(prefix="/api/v1", tags=["admins"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/admins/register", response_model=AdminResponse)
@limiter.limit("5/minute")
async def register_admin(
    request: Request,
    admin_data: AdminRegister, db: Annotated[Session, Depends(get_db)]
):
    # Sanitize inputs
    username = admin_data.username.strip()
    email = admin_data.email.strip().lower()
    
    existing = (
        db.query(Admin)
        .filter(
            (Admin.username == username) | (Admin.email == email)
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Username or email already registered"
        )

    invite_code = InviteService.validate_invite_code(db, admin_data.invite_code)
    if not invite_code:
        raise HTTPException(status_code=403, detail="Invalid invite code")

    new_admin = Admin(
        username=username,
        email=email,
        password_hash=hash_password(admin_data.password),
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    InviteService.mark_as_used(db, invite_code)

    return new_admin


@router.post("/admins/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    admin_data: AdminLogin, db: Annotated[Session, Depends(get_db)]
):
    # Sanitize inputs
    username = admin_data.username.strip()
    
    admin = db.query(Admin).filter(Admin.username == username).first()
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
    return InviteService.create_invite_code(
        db, current_admin.id, invite_data.expires_hours
    )


@router.get("/admin/invites", response_model=InviteCodeListResponse)
async def list_invite_codes(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    codes = InviteService.get_all_codes(db)
    return InviteCodeListResponse(codes=codes, total=len(codes))


@router.delete("/admin/invites/{code_id}")
async def delete_invite_code(
    code_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
):
    success = InviteService.delete_invite_code(db, code_id)
    if not success:
        # Check if it exists at all to return 404 vs 400
        invite_code = db.query(AdminInviteCode).filter(AdminInviteCode.id == code_id).first()
        if not invite_code:
            raise HTTPException(status_code=404, detail="Invite code not found")
        raise HTTPException(status_code=400, detail="Cannot delete used invite code")

    return {"message": f"Invite code {code_id} deleted successfully"}


@router.post("/admins/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    reset_data: AdminPasswordReset,
    db: Annotated[Session, Depends(get_db)],
):
    username = reset_data.username.strip()

    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    invite_code = InviteService.validate_invite_code(db, reset_data.invite_code)
    is_env_code = False

    if not invite_code:
        reset_code_env = os.getenv("RESET_INVITE_CODE", "").strip()
        if reset_code_env and reset_data.invite_code == reset_code_env:
            is_env_code = True

    if not invite_code and not is_env_code:
        raise HTTPException(
            status_code=403,
            detail="Invalid, expired, or already used invite code",
        )

    admin.password_hash = hash_password(reset_data.new_password)
    if invite_code:
        InviteService.mark_as_used(db, invite_code)
    db.commit()

    return {"message": "Password reset successfully"}
