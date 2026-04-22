import os
import urllib.request
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    ort = None


MODEL_URL = (
    "https://huggingface.co/garavv/arcface-onnx/resolve/main/arc.onnx?download=true"
)


def download_model(model_dir: str = "models") -> bool:
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "arcface.onnx")

    if os.path.exists(model_path):
        print(f"Model already exists at {model_path}")
        return True

    print(f"Downloading ArcFace model from {MODEL_URL}...")
    print("This may take a few minutes (size: ~130 MB)...")

    try:
        urllib.request.urlretrieve(MODEL_URL, model_path)
        print(f"Model downloaded successfully to {model_path}")
        return True
    except Exception as e:
        print(f"Failed to download model: {e}")
        return False


class FaceRecognitionService:
    def __init__(self, model_dir: str = "models", auto_download: bool = True) -> None:
        self.model_dir = model_dir
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5
        )
        self.embedding_size = 512
        self.session = None
        self._input_name = None

        embedding_model_path = os.path.join(model_dir, "arcface.onnx")
        self._load_model(embedding_model_path, auto_download)

    def _load_model(self, model_path: str, auto_download: bool) -> None:
        if ort is None:
            print("WARNING: onnxruntime not installed, falling back to histogram-based face recognition")
            return

        if os.path.exists(model_path):
            try:
                self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
                self._input_name = self.session.get_inputs()[0].name
                print(f"ArcFace model loaded from {model_path}")
                return
            except Exception as e:
                print(f"WARNING: Failed to load ArcFace model from {model_path}: {e}")
                print("Falling back to histogram-based face recognition")

        if auto_download:
            if download_model(self.model_dir):
                try:
                    self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
                    self._input_name = self.session.get_inputs()[0].name
                    print(f"ArcFace model loaded from {model_path}")
                    return
                except Exception as e:
                    print(f"WARNING: Downloaded model failed to load: {e}")

        print(
            f"WARNING: ArcFace model not available, using fallback histogram method"
        )

    @property
    def model_name(self) -> str:
        return "arcface_onnx" if self.session is not None else "histogram_fallback"

    @property
    def model_status(self) -> str:
        if self.session is not None:
            model_path = os.path.join(self.model_dir, "arcface.onnx")
            return f"ArcFace ONNX (512-dim) loaded from {model_path}"
        else:
            return "Histogram fallback (64-bin grayscale) — ArcFace model unavailable"

    def detect_faces(
        self, image: np.ndarray, conf_threshold: float = 0.5
    ) -> list[tuple[int, int, int, int]]:
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(image_rgb)

        faces: list[tuple[int, int, int, int]] = []
        if results.detections:
            for detection in results.detections:
                if detection.score[0] < conf_threshold:
                    continue

                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)

                x = max(0, x)
                y = max(0, y)
                width = min(width, w - x)
                height = min(height, h - y)

                if width > 20 and height > 20:
                    faces.append((x, y, width, height))

        return faces

    def get_face_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        if face_image is None or face_image.size == 0:
            return None

        try:
            if self.session is not None:
                face_resized = cv2.resize(face_image, (112, 112))
                face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
                face_float = face_rgb.astype(np.float32)
                face_normalized = (face_float - 127.5) / 128.0
                input_blob = face_normalized[np.newaxis, ...]
                outputs = self.session.run(None, {self._input_name: input_blob})
                embedding = outputs[0].flatten()
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                return embedding.astype(np.float64)
            else:
                face_resized = cv2.resize(face_image, (96, 96))
                face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
                face_equalized = cv2.equalizeHist(face_gray)
                hist = cv2.calcHist([face_equalized], [0], None, [64], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                target_size = 512
                if len(hist) < target_size:
                    embedding = np.pad(hist, (0, target_size - len(hist)), "constant")
                else:
                    embedding = hist[:target_size]
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                return embedding.astype(np.float64)

        except Exception as e:
            print(f"Error extracting face embedding: {e}")
            return None

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
            return np.array([], dtype=np.float64)

        similarities = known_embeddings @ query_embedding
        return similarities
