import os

import numpy as np

from .crypto import decrypt, encrypt, is_encrypted

EMBEDDING_DIM = 512
EMBEDDING_DTYPE = np.float32
EMBEDDING_BYTES_FLOAT32 = EMBEDDING_DIM * 4  # 2048
EMBEDDING_BYTES_FLOAT64 = EMBEDDING_DIM * 8  # 4096

_encryption_key: str | None = None


def _get_encryption_key() -> str:
    global _encryption_key
    if _encryption_key is not None:
        return _encryption_key
    key = os.getenv("ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("ENCRYPTION_KEY environment variable is not set")
    _encryption_key = key
    return _encryption_key


def set_encryption_key(key: str) -> None:
    global _encryption_key
    _encryption_key = key


def serialize_embedding(embedding: np.ndarray) -> bytes:
    raw = embedding.astype(EMBEDDING_DTYPE).tobytes()
    return encrypt(raw, _get_encryption_key())


def deserialize_embedding(data: bytes) -> np.ndarray:
    if is_encrypted(data):
        raw = decrypt(data, _get_encryption_key())
        size = len(raw)
        if size == EMBEDDING_BYTES_FLOAT32:
            return np.frombuffer(raw, dtype=np.float32).copy()
        if size == EMBEDDING_BYTES_FLOAT64:
            return np.frombuffer(raw, dtype=np.float64).astype(np.float32)
        raise ValueError(
            f"Invalid decrypted embedding size: {size} bytes "
            f"(expected {EMBEDDING_BYTES_FLOAT32} or {EMBEDDING_BYTES_FLOAT64})"
        )

    size = len(data)
    if size == EMBEDDING_BYTES_FLOAT32:
        return np.frombuffer(data, dtype=np.float32).copy()
    if size == EMBEDDING_BYTES_FLOAT64:
        arr = np.frombuffer(data, dtype=np.float64)
        return arr.astype(np.float32)
    raise ValueError(
        f"Invalid embedding size: {size} bytes "
        f"(expected {EMBEDDING_BYTES_FLOAT32} for float32 "
        f"or {EMBEDDING_BYTES_FLOAT64} for float64)"
    )


def validate_embedding(data: bytes) -> bool:
    if is_encrypted(data):
        try:
            raw = decrypt(data, _get_encryption_key())
            return len(raw) in (EMBEDDING_BYTES_FLOAT32, EMBEDDING_BYTES_FLOAT64)
        except Exception:
            return False
    return len(data) in (EMBEDDING_BYTES_FLOAT32, EMBEDDING_BYTES_FLOAT64)
