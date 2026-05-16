import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..models import AdminInviteCode


class InviteService:
    @staticmethod
    def create_invite_code(
        db: Session,
        created_by: int,
        expires_hours: int = 24,
    ) -> AdminInviteCode:
        code = secrets.token_urlsafe(16)[:16]
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

        invite_code = AdminInviteCode(
            code=code,
            created_by=created_by,
            expires_at=expires_at,
        )
        db.add(invite_code)
        db.commit()
        db.refresh(invite_code)
        return invite_code

    @staticmethod
    def validate_invite_code(db: Session, code: str) -> Optional[AdminInviteCode]:
        invite_code = (
            db.query(AdminInviteCode).filter(AdminInviteCode.code == code).first()
        )
        if not invite_code:
            return None
        if invite_code.is_used:
            return None
        if invite_code.expires_at and invite_code.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None
        return invite_code

    @staticmethod
    def delete_invite_code(db: Session, code_id: int) -> bool:
        invite_code = (
            db.query(AdminInviteCode).filter(AdminInviteCode.id == code_id).first()
        )
        if not invite_code or invite_code.is_used:
            return False
        db.delete(invite_code)
        db.commit()
        return True

    @staticmethod
    def get_all_codes(db: Session) -> list[AdminInviteCode]:
        return db.query(AdminInviteCode).all()

    @staticmethod
    def mark_as_used(db: Session, invite_code: AdminInviteCode) -> None:
        invite_code.is_used = True
        invite_code.used_at = datetime.now(timezone.utc)
        db.commit()
