from fastapi import Request

from .auth import get_current_admin
from .database import get_db


def get_face_service(request: Request):
    from .services.face_service import FaceRecognitionService

    service = getattr(request.app.state, "face_service", None)
    if service is None:
        import os

        model_dir = os.getenv("MODEL_DIR", "models")
        service = FaceRecognitionService(model_dir=model_dir)
        request.app.state.face_service = service
    return service


def get_email_service(request: Request):
    return request.app.state.email_service