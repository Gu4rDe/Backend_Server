import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..models import Admin, PasswordResetToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_EXPIRE_HOURS = 1
RATE_LIMIT_MINUTES = 5
TOKEN_LENGTH = 8
TOKEN_ALPHABET = string.ascii_letters + string.digits


class TokenService:
    @staticmethod
    def is_rate_limited(admin_id: int, db: Session) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=RATE_LIMIT_MINUTES)
        recent = db.query(PasswordResetToken).filter(
            PasswordResetToken.admin_id == admin_id,
            PasswordResetToken.created_at >= cutoff,
        ).first()
        return recent is not None

    @staticmethod
    def generate_reset_token(admin_id: int, db: Session) -> str:
        db.query(PasswordResetToken).filter(
            PasswordResetToken.admin_id == admin_id,
            PasswordResetToken.is_used == False,  # noqa: E712
        ).update({"is_used": True})

        token = "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(TOKEN_LENGTH))
        token_hash = pwd_context.hash(token)

        reset_token = PasswordResetToken(
            token_hash=token_hash,
            admin_id=admin_id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
        )
        db.add(reset_token)
        db.commit()
        db.refresh(reset_token)

        return token

    @staticmethod
    def validate_reset_token(token: str, db: Session) -> Optional[Admin]:
        tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.is_used == False,  # noqa: E712
        ).all()

        matching_token: PasswordResetToken | None = None
        for t in tokens:
            if pwd_context.verify(token, t.token_hash):
                matching_token = t
                break

        if matching_token is None:
            return None

        if matching_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None

        admin = db.query(Admin).filter(Admin.id == matching_token.admin_id).first()
        if admin is None:
            return None

        return admin

    @staticmethod
    def mark_token_used(token_str: str, db: Session) -> None:
        tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.is_used == False,  # noqa: E712
        ).all()

        for t in tokens:
            if pwd_context.verify(token_str, t.token_hash):
                t.is_used = True
                db.commit()
                return