from fastapi import APIRouter

from .admins import router as admins_router
from .employees import router as employees_router
from .faces import router as faces_router
from .settings import router as settings_router

__all__ = ["admins_router", "employees_router", "faces_router", "settings_router"]
