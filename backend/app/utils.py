import cv2
import numpy as np
from fastapi import HTTPException


def decode_image(contents: bytes) -> np.ndarray:
    """Decode image bytes into a numpy array (BGR)."""
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    return img


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize and truncate string input."""
    if not value:
        return ""
    return value.strip()[:max_length]
