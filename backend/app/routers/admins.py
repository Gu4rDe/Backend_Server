import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_admin, hash_password, verify_password
from ..database import get_db
from ..deps import get_email_service
from ..models import Admin, AdminInviteCode
from ..services.email_service import EmailService
from ..services.invite_service import InviteService
from ..services.token_service import TokenService
from ..schemas import (
    AdminLogin,
    AdminPasswordReset,
    AdminRegister,
    AdminResponse,
    ForgotPasswordRequest,
    InviteCodeCreate,
    InviteCodeListResponse,
    InviteCodeResponse,
    MessageResponse,
    TokenResponse,
    VerifyResetTokenRequest,
    VerifyResetTokenResponse,
)

router = APIRouter(prefix="/api/v1", tags=["admins"])
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


@router.post("/admins/register", response_model=AdminResponse)
@limiter.limit("5/minute")
async def register_admin(
    request: Request,
    admin_data: AdminRegister, db: Annotated[Session, Depends(get_db)]
):
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

    initial_invite_code = InviteService.validate_invite_code(db, admin_data.invite_code)
    if not initial_invite_code:
        raise HTTPException(
            status_code=403, detail="Invalid or expired invite code"
        )

    new_admin = Admin(
        username=username,
        email=email,
        password_hash=hash_password(admin_data.password),
    )
    db.add(new_admin)
    InviteService.mark_as_used(db, initial_invite_code)
    db.commit()
    db.refresh(new_admin)

    return new_admin


@router.post("/admins/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    admin_data: AdminLogin, db: Annotated[Session, Depends(get_db)]
):
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
        invite_code = db.query(AdminInviteCode).filter(AdminInviteCode.id == code_id).first()
        if not invite_code:
            raise HTTPException(status_code=404, detail="Invite code not found")
        raise HTTPException(status_code=400, detail="Cannot delete used invite code")

    return {"message": f"Invite code {code_id} deleted successfully"}


@router.post("/admins/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
):
    username = data.username.strip()

    admin = db.query(Admin).filter(
        (Admin.username == username) | (Admin.email == username.lower())
    ).first()
    if admin and admin.email:
        if TokenService.is_rate_limited(admin.id, db):
            return {"message": "If the account exists, a reset email has been sent"}
        token = TokenService.generate_reset_token(admin.id, db)
        try:
            await email_service.send_reset_email(admin.email, token)
        except Exception:
            logger.exception("Failed to send reset email to %s", admin.email)

    return {"message": "If the account exists, a reset email has been sent"}


@router.post("/admins/verify-reset-token", response_model=VerifyResetTokenResponse)
@limiter.limit("5/minute")
async def verify_reset_token(
    request: Request,
    data: VerifyResetTokenRequest,
    db: Annotated[Session, Depends(get_db)],
):
    admin = TokenService.validate_reset_token(data.token, db)
    if admin:
        return VerifyResetTokenResponse(valid=True)
    return VerifyResetTokenResponse(valid=False)


@router.post("/admins/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    reset_data: AdminPasswordReset,
    db: Annotated[Session, Depends(get_db)],
):
    admin = TokenService.validate_reset_token(reset_data.token, db)
    if not admin:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token",
        )

    admin.password_hash = hash_password(reset_data.new_password)
    TokenService.mark_token_used(reset_data.token, db)
    db.commit()

    return {"message": "Password reset successfully"}