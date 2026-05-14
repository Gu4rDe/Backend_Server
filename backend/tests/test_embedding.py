import numpy as np
import pytest

from app.services.embedding import (
    EMBEDDING_BYTES_FLOAT32,
    EMBEDDING_BYTES_FLOAT64,
    EMBEDDING_DIM,
    deserialize_embedding,
    serialize_embedding,
    validate_embedding,
)


def test_serialize_float32():
    emb = np.random.randn(EMBEDDING_DIM).astype(np.float32)
    data = serialize_embedding(emb)
    assert len(data) == EMBEDDING_BYTES_FLOAT32
    result = deserialize_embedding(data)
    np.testing.assert_array_almost_equal(emb, result, decimal=6)


def test_serialize_float64_input():
    emb = np.random.randn(EMBEDDING_DIM).astype(np.float64)
    data = serialize_embedding(emb)
    assert len(data) == EMBEDDING_BYTES_FLOAT32
    result = deserialize_embedding(data)
    np.testing.assert_array_almost_equal(emb.astype(np.float32), result, decimal=6)


def test_deserialize_float32():
    emb = np.random.randn(EMBEDDING_DIM).astype(np.float32)
    data = emb.tobytes()
    result = deserialize_embedding(data)
    assert result.dtype == np.float32
    assert result.shape == (EMBEDDING_DIM,)
    np.testing.assert_array_almost_equal(emb, result, decimal=6)


def test_deserialize_float64_legacy():
    emb = np.random.randn(EMBEDDING_DIM).astype(np.float64)
    data = emb.tobytes()
    assert len(data) == EMBEDDING_BYTES_FLOAT64
    result = deserialize_embedding(data)
    assert result.dtype == np.float32
    assert result.shape == (EMBEDDING_DIM,)
    expected = emb.astype(np.float32)
    np.testing.assert_array_almost_equal(expected, result, decimal=6)


def test_deserialize_invalid_size():
    with pytest.raises(ValueError, match="Invalid embedding size"):
        deserialize_embedding(b"\x00" * 100)


def test_validate_embedding_float32():
    data = np.zeros(EMBEDDING_DIM, dtype=np.float32).tobytes()
    assert validate_embedding(data) is True


def test_validate_embedding_float64():
    data = np.zeros(EMBEDDING_DIM, dtype=np.float64).tobytes()
    assert validate_embedding(data) is True


def test_validate_embedding_invalid():
    assert validate_embedding(b"\x00" * 100) is False
    assert validate_embedding(b"") is False


def test_round_trip():
    original = np.random.randn(EMBEDDING_DIM).astype(np.float32)
    original = original / np.linalg.norm(original)
    data = serialize_embedding(original)
    restored = deserialize_embedding(data)
    norm_diff = abs(np.linalg.norm(original) - np.linalg.norm(restored))
    assert norm_diff < 1e-6