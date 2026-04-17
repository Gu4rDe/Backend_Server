import os
from typing import Annotated

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..auth import get_current_admin
from ..database import get_db
from ..models import Admin, Employee
from ..services.face_service import FaceRecognitionService

router = APIRouter(prefix="/api/v1", tags=["faces"])

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
face_service = FaceRecognitionService(model_dir=os.getenv("MODEL_DIR", "models"))


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
        faces = face_service.detect_faces(img)

        if len(faces) == 0:
            return {
                "faces_detected": 0,
                "results": [],
                "message": "No faces detected in the image",
            }

        known_faces = db.query(Employee).all()

        known_embeddings = np.array(
            [
                np.frombuffer(record.embedding, dtype=np.float64)
                for record in known_faces
            ]
        )
        known_records = known_faces

        results = []

        for x, y, w, h in faces:
            face_img = img[y : y + h, x : x + w]
            embedding = face_service.get_face_embedding(face_img)

            if embedding is None:
                continue

            similarities = face_service.compare_faces_batch(embedding, known_embeddings)

            matches = []
            for i, similarity in enumerate(similarities):
                if similarity > 0.4:
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
            results.append({"bbox": [x, y, w, h], "matches": matches})

        return {
            "faces_detected": len(faces),
            "results": results,
            "message": f"Processed {len(faces)} face(s)",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
