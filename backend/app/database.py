import os
import secrets
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

ENV_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


def ensure_env_file() -> None:
    if not os.path.exists(ENV_FILE_PATH):
        secret_key = secrets.token_urlsafe(32)
        invite_code = secrets.token_urlsafe(16)[:16]

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
                "INITIAL_INVITE_CODE=",
                f"INITIAL_INVITE_CODE={invite_code}",
            )

            with open(ENV_FILE_PATH, "w") as f:
                f.write(content)
        else:
            with open(ENV_FILE_PATH, "w") as f:
                f.write(f"SECRET_KEY={secret_key}\n")
                f.write("DATABASE_URL=sqlite:///./data/faces.db\n")
                f.write("MODEL_DIR=models\n")
                f.write(f"INITIAL_INVITE_CODE={invite_code}\n")

        print(
            f"Created .env file with generated SECRET_KEY and INITIAL_INVITE_CODE at {ENV_FILE_PATH}"
        )


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/faces.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
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
