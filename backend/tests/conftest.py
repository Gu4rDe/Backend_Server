import os

os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["INITIAL_INVITE_CODE"] = "testinvitecode1234"
os.environ["MODEL_DIR"] = "models"
os.environ["ENCRYPTION_KEY"] = "n5RB92P5EAO1cpfUkhhKBGS1LKMt7gmwMobJPU7-pTI="
os.environ["SMTP_HOST"] = ""
os.environ["SMTP_PORT"] = "587"
os.environ["SMTP_USER"] = ""
os.environ["SMTP_PASSWORD"] = ""
os.environ["SMTP_FROM"] = "test@example.com"
os.environ["FRONTEND_URL"] = "http://localhost:3000"

import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import create_access_token, hash_password
from app.database import get_db
from app.deps import get_email_service
from app.main import app
from app.models import Admin, Base
from app.services.email_service import EmailService

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def override_get_email_service():
    mock_service = AsyncMock(spec=EmailService)
    mock_service.is_configured = True
    mock_service.send_reset_email = AsyncMock()
    return mock_service


app.dependency_overrides[get_email_service] = override_get_email_service


@pytest.fixture(autouse=True)
def setup_database():
    from app.routers.admins import limiter

    Base.metadata.create_all(bind=test_engine)
    limiter.reset()
    yield
    limiter.reset()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_admin(db):
    admin = Admin(
        username="testadmin",
        email="testadmin@example.com",
        password_hash=hash_password("testpassword123"),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def auth_headers(test_admin):
    token = create_access_token(data={"sub": str(test_admin.id)})
    return {"Authorization": f"Bearer {token}"}
