import os
import urllib.request
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np


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

        embedding_model_path = os.path.join(model_dir, "arcface.onnx")
        if os.path.exists(embedding_model_path):
            self.embedding_net = cv2.dnn.readNetFromONNX(embedding_model_path)
            print(f"ArcFace model loaded from {embedding_model_path}")
        elif auto_download:
            if download_model(model_dir):
                self.embedding_net = cv2.dnn.readNetFromONNX(embedding_model_path)
                print(f"ArcFace model loaded from {embedding_model_path}")
            else:
                self.embedding_net = None
        else:
            self.embedding_net = None
            print(
                f"WARNING: ArcFace model not found at {embedding_model_path}, using fallback histogram method"
            )

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
            if self.embedding_net is not None:
                face_resized = cv2.resize(face_image, (112, 112))
                face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
                face_float = face_rgb.astype(np.float32)
                face_normalized = (face_float - 127.5) / 128.0
                input_blob = face_normalized[np.newaxis, ...]
                self.embedding_net.setInput(input_blob)
                embedding = self.embedding_net.forward()
                embedding = embedding.flatten()
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
