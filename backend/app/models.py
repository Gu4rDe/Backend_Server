from datetime import datetime
from typing import Annotated

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Admin(id={self.id}, username='{self.username}')>"


class AdminInviteCode(Base):
    __tablename__ = "admin_invite_codes"

    id = Column(Integer, primary_key=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("admins.id", ondelete="CASCADE"), nullable=True)
    used_by = Column(Integer, nullable=True)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<AdminInviteCode(id={self.id}, code='{self.code}', is_used={self.is_used})>"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    employee_id = Column(String(50), default="", index=True)
    username = Column(String(150), nullable=False, index=True)
    email = Column(String(100), default="")
    phone = Column(String(30), default="")
    department = Column(String(100), default="")
    position = Column(String(100), default="")
    location = Column(String(100), default="")
    hire_date = Column(String(20), default="")
    is_active = Column(Boolean, default=True, nullable=False)
    access_enabled = Column(Boolean, default=True, nullable=False)
    photo_path = Column(String(255), default="")
    embedding = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, username='{self.username}')>"


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True)
    theme = Column(String(20), default="dark")
    fullscreen = Column(Boolean, default=False)
    camera_resolution = Column(String(20), default="Full HD")
    camera_fps = Column(Integer, default=30)
    sound_notifications = Column(Boolean, default=True)
    access_notifications = Column(Boolean, default=True)
    match_threshold = Column(Float, default=0.4)
    two_factor_enabled = Column(Boolean, default=False)
    auto_backup = Column(Boolean, default=False)
    backend_url = Column(String(255), default="http://localhost:8000")
    connection_timeout = Column(Integer, default=10)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<AppSettings(id={self.id})>"
