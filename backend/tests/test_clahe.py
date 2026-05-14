import numpy as np
import pytest

from app.services.face_service import apply_clahe


def test_clahe_preserves_shape():
    img = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
    result = apply_clahe(img)
    assert result.shape == img.shape
    assert result.dtype == img.dtype


def test_clahe_custom_params():
    img = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
    result = apply_clahe(img, clip_limit=3.0, tile_grid_size=(4, 4))
    assert result.shape == img.shape


def test_clahe_returns_none_safe():
    assert apply_clahe(None) is None
    assert apply_clahe(np.array([])).size == 0


def test_clahe_enhances_low_contrast():
    dark = np.full((100, 100, 3), 30, dtype=np.uint8)
    result = apply_clahe(dark)
    assert result.shape == dark.shape
    mean_original = dark.mean()
    mean_enhanced = result.mean()
    assert mean_enhanced > mean_original