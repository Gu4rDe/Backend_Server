import numpy as np
import pytest

from app.services.crypto import encrypt, generate_encryption_key, is_encrypted
from app.services.embedding import (
    EMBEDDING_BYTES_FLOAT32,
    EMBEDDING_BYTES_FLOAT64,
    EMBEDDING_DIM,
    deserialize_embedding,
    serialize_embedding,
    set_encryption_key,
    validate_embedding,
)

TEST_KEY = "n5RB92P5EAO1cpfUkhhKBGS1LKMt7gmwMobJPU7-pTI="


@pytest.fixture(autouse=True)
def _set_key():
    set_encryption_key(TEST_KEY)
    yield
    set_encryption_key(None)


def test_serialize_produces_encrypted_data():
    emb = np.random.randn(EMBEDDING_DIM).astype(np.float32)
    data = serialize_embedding(emb)
    assert is_encrypted(data)
    assert data[0] == 0x01


def test_round_trip_encrypted():
    emb = np.random.randn(EMBEDDING_DIM).astype(np.float32)
    emb = emb / np.linalg.norm(emb)
    data = serialize_embedding(emb)
    result = deserialize_embedding(data)
    np.testing.assert_array_almost_equal(emb, result, decimal=6)


def test_serialize_float64_input():
    emb = np.random.randn(EMBEDDING_DIM).astype(np.float64)
    data = serialize_embedding(emb)
    result = deserialize_embedding(data)
    np.testing.assert_array_almost_equal(emb.astype(np.float32), result, decimal=6)


def test_different_serializations_differ():
    emb = np.random.randn(EMBEDDING_DIM).astype(np.float32)
    d1 = serialize_embedding(emb)
    d2 = serialize_embedding(emb)
    assert d1 != d2


def test_deserialize_float32_legacy():
    emb = np.random.randn(EMBEDDING_DIM).astype(np.float32)
    raw = emb.tobytes()
    result = deserialize_embedding(raw)
    assert result.dtype == np.float32
    np.testing.assert_array_almost_equal(emb, result, decimal=6)


def test_deserialize_float64_legacy():
    emb = np.random.randn(EMBEDDING_DIM).astype(np.float64)
    raw = emb.tobytes()
    assert len(raw) == EMBEDDING_BYTES_FLOAT64
    result = deserialize_embedding(raw)
    assert result.dtype == np.float32
    np.testing.assert_array_almost_equal(emb.astype(np.float32), result, decimal=6)


def test_deserialize_invalid_size():
    with pytest.raises(ValueError, match="Invalid embedding size"):
        deserialize_embedding(b"\x00" * 100)


def test_validate_embedding_encrypted():
    emb = np.random.randn(EMBEDDING_DIM).astype(np.float32)
    data = serialize_embedding(emb)
    assert validate_embedding(data) is True


def test_validate_embedding_float32_legacy():
    data = np.zeros(EMBEDDING_DIM, dtype=np.float32).tobytes()
    assert validate_embedding(data) is True


def test_validate_embedding_float64_legacy():
    data = np.zeros(EMBEDDING_DIM, dtype=np.float64).tobytes()
    assert validate_embedding(data) is True


def test_validate_embedding_invalid():
    assert validate_embedding(b"\x00" * 100) is False
    assert validate_embedding(b"") is False


def test_round_trip_norm_preserved():
    emb = np.random.randn(EMBEDDING_DIM).astype(np.float32)
    emb = emb / np.linalg.norm(emb)
    data = serialize_embedding(emb)
    restored = deserialize_embedding(data)
    norm_diff = abs(np.linalg.norm(emb) - np.linalg.norm(restored))
    assert norm_diff < 1e-6


def test_average_embeddings_produces_unit_vector():
    from app.services.face_service import FaceRecognitionService

    embeddings = [np.random.randn(EMBEDDING_DIM).astype(np.float32) for _ in range(5)]
    for i, e in enumerate(embeddings):
        embeddings[i] = e / np.linalg.norm(e)

    result = FaceRecognitionService.average_embeddings(embeddings)
    assert result.dtype == np.float32
    assert abs(np.linalg.norm(result) - 1.0) < 1e-6


def test_average_embeddings_single_vector():
    from app.services.face_service import FaceRecognitionService

    emb = np.random.randn(EMBEDDING_DIM).astype(np.float32)
    emb = emb / np.linalg.norm(emb)
    result = FaceRecognitionService.average_embeddings([emb])
    np.testing.assert_array_almost_equal(result, emb, decimal=6)


def test_average_embeddings_raises_on_empty():
    from app.services.face_service import FaceRecognitionService

    with pytest.raises(ValueError, match="No embeddings"):
        FaceRecognitionService.average_embeddings([])