import base64
import logging
import os
import secrets
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

load_dotenv()

logger = logging.getLogger(__name__)

ENV_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

DEFAULT_DATABASE_URL = "sqlite:///./data/faces.db"


def ensure_env_file() -> None:
    if not os.path.exists(ENV_FILE_PATH):
        logger.info("Checking for .env file...")
        logger.info(".env file not found, creating new one...")

        secret_key = secrets.token_urlsafe(32)
        encryption_key = base64.b64encode(os.urandom(32)).decode("utf-8")
        invite_code = secrets.token_urlsafe(16)[:16]
        reset_code = secrets.token_urlsafe(16)[:16]

        logger.info("Generated SECRET_KEY")
        logger.info("Generated ENCRYPTION_KEY")
        logger.info("Generated INITIAL_INVITE_CODE: %s", invite_code)
        logger.info("Generated RESET_INVITE_CODE: %s", reset_code)

        example_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".env.example"
        )

        if os.path.exists(example_path):
            with open(example_path, "r") as f:
                content = f.read()

            content = content.replace(
                "SECRET_KEY=your-secret-key-change-in-production",
                f"SECRET_KEY={secret_key}",
            )

            content = content.replace(
                "ENCRYPTION_KEY=your-encryption-key-base64-change-in-production",
                f"ENCRYPTION_KEY={encryption_key}",
            )

            content = content.replace(
                "INITIAL_INVITE_CODE=\n",
                f"INITIAL_INVITE_CODE={invite_code}\n",
            )

            content = content.replace(
                "RESET_INVITE_CODE=\n",
                f"RESET_INVITE_CODE={reset_code}\n",
            )

            with open(ENV_FILE_PATH, "w") as f:
                f.write(content)
        else:
            with open(ENV_FILE_PATH, "w") as f:
                f.write(f"SECRET_KEY={secret_key}\n")
                f.write(f"DATABASE_URL={DEFAULT_DATABASE_URL}\n")
                f.write(f"ENCRYPTION_KEY={encryption_key}\n")
                f.write(f"INITIAL_INVITE_CODE={invite_code}\n")
                f.write(f"RESET_INVITE_CODE={reset_code}\n")

        logger.info("Created .env file at %s", ENV_FILE_PATH)
    else:
        logger.info(".env file already exists, skipping creation")


DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Path("data").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
