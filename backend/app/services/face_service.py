import logging
from dataclasses import dataclass

import cv2
import numpy as np

try:
    from insightface.app import FaceAnalysis

    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class FaceResult:
    bbox: list[int]
    embedding: np.ndarray
    confidence: float


def apply_clahe(
    image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: tuple = (8, 8)
) -> np.ndarray:
    if image is None or image.size == 0:
        return image
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


class FaceRecognitionService:
    def __init__(self, model_dir: str = "models") -> None:
        self.model_dir = model_dir
        self.embedding_size = 512
        self._initialized = False

        self.app = None

        if INSIGHTFACE_AVAILABLE:
            try:
                self.app = FaceAnalysis(
                    name="buffalo_l", providers=["CPUExecutionProvider"]
                )
                self.app.prepare(ctx_id=-1, det_size=(640, 640))
                self._initialized = True
                logger.info("Face recognition service initialized with insightface")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize insightface: {e}")

        logger.warning("Face recognition service not initialized — no models available")

    @property
    def model_status(self) -> str:
        if self._initialized:
            return "insightface buffalo_l (SCRFD + ArcFace R50)"
        return "No models loaded"

    def detect_and_embed(
        self, image: np.ndarray, conf_threshold: float = 0.5
    ) -> list[FaceResult]:
        if not self._initialized:
            raise RuntimeError("Face recognition service not initialized")
        if image is None or image.size == 0:
            return []

        enhanced = apply_clahe(image)
        faces = self.app.get(enhanced)
        results: list[FaceResult] = []
        for face in faces:
            if face.det_score < conf_threshold:
                continue
            bbox = face.bbox.astype(int).tolist()
            x1, y1, x2, y2 = bbox
            bbox_xywh = [x1, y1, x2 - x1, y2 - y1]
            embedding = face.embedding.astype(np.float32)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            results.append(
                FaceResult(bbox=[int(x) for x in bbox_xywh], embedding=embedding, confidence=float(face.det_score))
            )
        return results

    def detect_faces(
        self, image: np.ndarray, conf_threshold: float = 0.5
    ) -> list[tuple[int, int, int, int]]:
        face_results = self.detect_and_embed(image, conf_threshold)
        return [tuple(f.bbox) for f in face_results]

    @staticmethod
    def average_embeddings(embeddings: list[np.ndarray]) -> np.ndarray:
        if not embeddings:
            raise ValueError("No embeddings provided for averaging")
        stacked = np.stack(embeddings, axis=0)
        mean = np.mean(stacked, axis=0)
        norm = np.linalg.norm(mean)
        if norm > 0:
            mean = mean / norm
        return mean.astype(np.float32)

    def compare_faces(
        self, emb1: np.ndarray, emb2: np.ndarray, threshold: float = 0.4
    ) -> bool:
        if emb1 is None or emb2 is None:
            return False
        if emb1.shape != emb2.shape:
            return False
        similarity = np.dot(emb1, emb2)
        return bool(similarity > threshold)

    def compare_faces_batch(
        self,
        query_embedding: np.ndarray,
        known_embeddings: np.ndarray,
        threshold: float = 0.4,
    ) -> np.ndarray:
        if known_embeddings.size == 0:
            return np.array([], dtype=np.float32)
        similarities = known_embeddings @ query_embedding
        return similarities