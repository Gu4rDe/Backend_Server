import logging
import os
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

try:
    from insightface.app import FaceAnalysis

    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False

try:
    import onnxruntime as ort
except ImportError:
    ort = None

logger = logging.getLogger(__name__)

SCRFD_MODEL_FILENAME = "det_10g.onnx"
ADAFACE_MODEL_FILENAME = "adaface_ir101.onnx"

ARCFACE_REFERENCE_POINTS = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)


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


def _estimate_transform(src_points: np.ndarray, dst_points: np.ndarray) -> np.ndarray:
    dx = src_points[:, 0].astype(np.float64)
    dy = src_points[:, 1].astype(np.float64)
    dx_mean = dx.mean()
    dy_mean = dy.mean()
    dst_x = dst_points[:, 0].astype(np.float64)
    dst_y = dst_points[:, 1].astype(np.float64)
    dst_x_mean = dst_x.mean()
    dst_y_mean = dst_y.mean()

    src_centered_x = dx - dx_mean
    src_centered_y = dy - dy_mean
    dst_centered_x = dst_x - dst_x_mean
    dst_centered_y = dst_y - dst_y_mean

    scale_num = np.sum(dst_centered_x * src_centered_x + dst_centered_y * src_centered_y)
    scale_den = np.sqrt(
        np.sum(src_centered_x**2 + src_centered_y**2)
        * np.sum(dst_centered_x**2 + dst_centered_y**2)
    )
    scale = scale_num / scale_den if scale_den > 0 else 1.0

    angle_num = np.sum(dst_centered_x * src_centered_y - dst_centered_y * src_centered_x)
    angle_den = np.sum(dst_centered_x * src_centered_x + dst_centered_y * src_centered_y)
    angle = np.arctan2(angle_num, angle_den)

    cos_a = np.cos(angle) * scale
    sin_a = np.sin(angle) * scale

    tx = dst_x_mean - cos_a * dx_mean - sin_a * dy_mean
    ty = dst_y_mean + sin_a * dx_mean - cos_a * dy_mean

    M = np.array([[cos_a, sin_a, tx], [-sin_a, cos_a, ty]], dtype=np.float32)
    return M


def norm_crop(image: np.ndarray, keypoints: np.ndarray, output_size: int = 112) -> np.ndarray:
    M = _estimate_transform(keypoints, ARCFACE_REFERENCE_POINTS)
    aligned = cv2.warpAffine(image, M, (output_size, output_size), borderValue=0.0)
    return aligned


class SCRFD:
    def __init__(self, model_path: str, input_size: tuple = (640, 640)):
        self.input_size = input_size
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self._output_names = [o.name for o in self.session.get_outputs()]

    def detect(
        self, image: np.ndarray, conf_threshold: float = 0.5
    ) -> list[tuple[list[int], float, np.ndarray]]:
        h, w = image.shape[:2]
        input_h, input_w = self.input_size
        scale_h = input_h / h
        scale_w = input_w / w

        resized = cv2.resize(image, (input_w, input_h))
        blob = resized.astype(np.float32)
        blob = (blob - 127.5) / 128.0
        blob = blob.transpose(2, 0, 1)[np.newaxis, ...]

        outputs = self.session.run(self._output_names, {self.input_name: blob})

        scores_list = outputs[0]
        boxes_list = outputs[1]
        kps_list = outputs[2] if len(outputs) > 2 else None

        results: list[tuple[list[int], float, np.ndarray]] = []

        if scores_list.ndim > 2:
            idx = np.where(scores_list[0, :, 0] > conf_threshold)[0]
            for i in idx:
                score = float(scores_list[0, i, 0])
                box = boxes_list[0, i, :]
                x1 = int(box[0] / scale_w)
                y1 = int(box[1] / scale_h)
                x2 = int(box[2] / scale_w)
                y2 = int(box[3] / scale_h)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)

                kps = None
                if kps_list is not None:
                    kp = kps_list[0, i, :].reshape(5, 2)
                    kp[:, 0] = kp[:, 0] / scale_w
                    kp[:, 1] = kp[:, 1] / scale_h
                    kps = kp

                bbox_xywh = [x1, y1, x2 - x1, y2 - y1]
                results.append((bbox_xywh, score, kps))

        return results


class FaceRecognitionService:
    def __init__(self, model_dir: str = "models") -> None:
        self.model_dir = model_dir
        self.embedding_size = 512
        self._initialized = False
        self._use_insightface = False

        self.app: Optional[FaceAnalysis] = None
        self.detector: Optional[SCRFD] = None
        self.recognition_session = None
        self._input_name = None

        if INSIGHTFACE_AVAILABLE:
            try:
                self.app = FaceAnalysis(
                    name="buffalo_l", providers=["CPUExecutionProvider"]
                )
                self.app.prepare(ctx_id=-1, det_size=(640, 640))
                self._use_insightface = True
                self._initialized = True
                logger.info("Face recognition service initialized with insightface")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize insightface: {e}")

        if ort is not None:
            scrfd_path = os.path.join(model_dir, SCRFD_MODEL_FILENAME)
            adaface_path = os.path.join(model_dir, ADAFACE_MODEL_FILENAME)
            self._load_detector(scrfd_path)
            self._load_recognition(adaface_path)

            if self.detector is not None and self.recognition_session is not None:
                self._initialized = True
                logger.info("Face recognition service initialized with ONNX fallback")

        if not self._initialized:
            logger.warning("Face recognition service not initialized — no models available")

    def _load_detector(self, model_path: str) -> None:
        if not os.path.exists(model_path):
            logger.error(f"SCRFD model not found at {model_path}")
            return
        try:
            self.detector = SCRFD(model_path)
            logger.info(f"SCRFD detector loaded from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load SCRFD detector: {e}")

    def _load_recognition(self, model_path: str) -> None:
        if not os.path.exists(model_path):
            logger.error(f"AdaFace model not found at {model_path}")
            return
        try:
            self.recognition_session = ort.InferenceSession(
                model_path, providers=["CPUExecutionProvider"]
            )
            self._input_name = self.recognition_session.get_inputs()[0].name
            logger.info(f"AdaFace model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load AdaFace model: {e}")

    @property
    def model_status(self) -> str:
        if self._use_insightface:
            return "insightface buffalo_l (SCRFD + ArcFace R50)"
        if self.detector is not None and self.recognition_session is not None:
            return "ONNX fallback (SCRFD + AdaFace IR-101)"
        return "No models loaded"

    def detect_and_embed(
        self, image: np.ndarray, conf_threshold: float = 0.5
    ) -> list[FaceResult]:
        if not self._initialized:
            raise RuntimeError("Face recognition service not initialized")
        if image is None or image.size == 0:
            return []

        enhanced = apply_clahe(image)

        if self._use_insightface:
            return self._detect_and_embed_insightface(enhanced, conf_threshold)
        return self._detect_and_embed_onnx(enhanced, conf_threshold)

    def _detect_and_embed_insightface(
        self, image: np.ndarray, conf_threshold: float
    ) -> list[FaceResult]:
        faces = self.app.get(image)
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

    def _detect_and_embed_onnx(
        self, image: np.ndarray, conf_threshold: float
    ) -> list[FaceResult]:
        detections = self.detector.detect(image, conf_threshold)
        results: list[FaceResult] = []
        for bbox_xywh, score, kps in detections:
            if kps is None:
                continue
            aligned = norm_crop(image, kps, output_size=112)
            embedding = self._get_embedding_onnx(aligned)
            if embedding is None:
                continue
            results.append(FaceResult(bbox=[int(v) for v in bbox_xywh], embedding=embedding, confidence=float(score)))
        return results

    def _get_embedding_onnx(self, aligned_face: np.ndarray) -> Optional[np.ndarray]:
        if aligned_face is None or aligned_face.size == 0:
            return None
        try:
            face_float = aligned_face.astype(np.float32)
            if face_float.shape[:2] != (112, 112):
                face_float = cv2.resize(face_float, (112, 112))
            face_normalized = (face_float - 127.5) / 128.0
            input_blob = face_normalized.transpose(2, 0, 1)[np.newaxis, ...].astype(np.float32)
            outputs = self.recognition_session.run(None, {self._input_name: input_blob})
            embedding = outputs[0].flatten()
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Error extracting face embedding: {e}")
            return None

    def detect_faces(
        self, image: np.ndarray, conf_threshold: float = 0.5
    ) -> list[tuple[int, int, int, int]]:
        face_results = self.detect_and_embed(image, conf_threshold)
        return [tuple(f.bbox) for f in face_results]

    def get_face_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        if not self._initialized:
            raise RuntimeError("Face recognition service not initialized")

        face_resized = cv2.resize(face_image, (112, 112))

        if self._use_insightface:
            face_float = face_resized.astype(np.float32)
            face_normalized = (face_float - 127.5) / 128.0
            input_blob = face_normalized.transpose(2, 0, 1)[np.newaxis, ...].astype(np.float32)
            try:
                outputs = self.recognition_session.run(None, {self._input_name: input_blob})
                embedding = outputs[0].flatten()
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                return embedding.astype(np.float32)
            except Exception as e:
                logger.error(f"Error extracting face embedding: {e}")
                return None

        return self._get_embedding_onnx(face_resized)

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