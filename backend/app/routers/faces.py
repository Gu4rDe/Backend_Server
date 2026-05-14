from typing import Annotated

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..auth import get_current_admin
from ..database import get_db
from ..deps import get_face_service
from ..models import Admin, AppSettings, Employee
from ..services.embedding import deserialize_embedding
from ..services.face_service import FaceRecognitionService

router = APIRouter(prefix="/api/v1", tags=["faces"])

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


def decode_image(contents: bytes) -> np.ndarray:
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    return img


@router.post("/faces/recognize")
async def recognize_file(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Admin, Depends(get_current_admin)],
    face_service: FaceRecognitionService = Depends(get_face_service),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Maximum size: {MAX_IMAGE_SIZE // (1024 * 1024)}MB",
        )

    try:
        img = decode_image(contents)
    except HTTPException:
        raise

    try:
        face_results = face_service.detect_and_embed(img)

        if len(face_results) == 0:
            return {
                "faces_detected": 0,
                "results": [],
                "message": "No faces detected in the image",
            }

        known_faces = db.query(Employee).filter(Employee.embedding.isnot(None)).all()

        if not known_faces:
            return {
                "faces_detected": len(face_results),
                "results": [
                    {"bbox": fr.bbox, "matches": []}
                    for fr in face_results
                ],
                "message": f"Processed {len(face_results)} face(s), no registered employees",
            }

        known_embeddings = np.array(
            [deserialize_embedding(record.embedding) for record in known_faces]
        )
        known_records = known_faces

        settings = db.query(AppSettings).first()
        threshold = settings.match_threshold if settings else 0.4

        results = []

        for fr in face_results:
            similarities = face_service.compare_faces_batch(
                fr.embedding, known_embeddings, threshold
            )

            matches = []
            for i, similarity in enumerate(similarities):
                if similarity > threshold:
                    record = known_records[i]
                    matches.append(
                        {
                            "id": record.id,
                            "username": record.username,
                            "position": record.position or "",
                            "department": record.department or "",
                            "email": record.email or "",
                            "phone": record.phone or "",
                            "location": record.location or "",
                            "hire_date": record.hire_date or "",
                            "is_active": record.is_active,
                            "access_enabled": record.access_enabled,
                            "similarity": float(similarity),
                        }
                    )

            matches.sort(key=lambda m: m["similarity"], reverse=True)
            results.append({"bbox": fr.bbox, "matches": matches})

        return {
            "faces_detected": len(face_results),
            "results": results,
            "message": f"Processed {len(face_results)} face(s)",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
