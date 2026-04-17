from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    invite_code: str = Field(..., min_length=8, max_length=32)


class AdminLogin(BaseModel):
    username: str
    password: str


class AdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmployeeCreate(BaseModel):
    employee_id: str = ""
    username: str
    email: str = ""
    phone: str = ""
    department: str = ""
    position: str = ""
    location: str = ""
    hire_date: str = ""
    is_active: bool = True
    access_enabled: bool = True


class EmployeeUpdate(BaseModel):
    employee_id: str | None = None
    username: str | None = None
    email: str | None = None
    phone: str | None = None
    department: str | None = None
    position: str | None = None
    location: str | None = None
    hire_date: str | None = None
    is_active: bool | None = None
    access_enabled: bool | None = None


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: str = ""
    username: str
    email: str = ""
    phone: str = ""
    department: str = ""
    position: str = ""
    location: str = ""
    hire_date: str = ""
    is_active: bool = True
    access_enabled: bool = True
    photo_path: str = ""
    created_at: datetime


class EmployeeStats(BaseModel):
    total: int
    active: int
    inactive: int


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    theme: str = "dark"
    fullscreen: bool = False
    camera_resolution: str = "Full HD"
    camera_fps: int = 30
    sound_notifications: bool = True
    access_notifications: bool = True
    match_threshold: float = 0.4
    two_factor_enabled: bool = False
    auto_backup: bool = False
    backend_url: str = "http://localhost:8000"
    connection_timeout: int = 10


class SettingsUpdate(BaseModel):
    theme: str | None = None
    fullscreen: bool | None = None
    camera_resolution: str | None = None
    camera_fps: int | None = None
    sound_notifications: bool | None = None
    access_notifications: bool | None = None
    match_threshold: float | None = None
    two_factor_enabled: bool | None = None
    auto_backup: bool | None = None
    backend_url: str | None = None
    connection_timeout: int | None = None


class InviteCodeCreate(BaseModel):
    expires_hours: int = 24


class InviteCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    created_by: int | None
    expires_at: datetime | None
    is_used: bool
    created_at: datetime


class InviteCodeListResponse(BaseModel):
    codes: list[InviteCodeResponse]
    total: int
