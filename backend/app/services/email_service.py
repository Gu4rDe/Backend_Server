import logging
import os
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


class EmailService:
    def __init__(self) -> None:
        self._configured = False
        self._fast_mail: FastMail | None = None
        self._frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self._from_email = os.getenv("SMTP_FROM", "noreply@example.com")

        smtp_host = os.getenv("SMTP_HOST", "smtp.yandex.ru")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")

        if not smtp_host or not smtp_user:
            logger.warning(
                "SMTP not configured (SMTP_HOST/SMTP_USER missing). "
                "Password reset emails will not be sent."
            )
            return

        conf = ConnectionConfig(
            MAIL_USERNAME=smtp_user,
            MAIL_PASSWORD=smtp_password,
            MAIL_FROM=self._from_email,
            MAIL_PORT=smtp_port,
            MAIL_SERVER=smtp_host,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            TEMPLATE_FOLDER=TEMPLATES_DIR,
        )
        self._fast_mail = FastMail(conf)
        self._configured = True
        logger.info("Email service configured: %s:%s", smtp_host, smtp_port)

    @property
    def is_configured(self) -> bool:
        return self._configured

    async def send_reset_email(self, to_email: str, token: str) -> None:
        if not self._configured:
            logger.error("Cannot send reset email: SMTP not configured")
            return

        message = MessageSchema(
            subject="Восстановление пароля",
            recipients=[to_email],
            template_body={"reset_code": token},
            subtype=MessageType.html,
        )

        try:
            await self._fast_mail.send_message(message, template_name="reset_email.html")
            logger.info("Reset email sent to %s", to_email)
        except Exception:
            logger.exception("Failed to send reset email to %s", to_email)