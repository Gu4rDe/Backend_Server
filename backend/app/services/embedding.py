import numpy as np

EMBEDDING_DIM = 512
EMBEDDING_DTYPE = np.float32
EMBEDDING_BYTES_FLOAT32 = EMBEDDING_DIM * 4  # 2048
EMBEDDING_BYTES_FLOAT64 = EMBEDDING_DIM * 8  # 4096


def serialize_embedding(embedding: np.ndarray) -> bytes:
    return embedding.astype(EMBEDDING_DTYPE).tobytes()


def deserialize_embedding(data: bytes) -> np.ndarray:
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
    return len(data) in (EMBEDDING_BYTES_FLOAT32, EMBEDDING_BYTES_FLOAT64)