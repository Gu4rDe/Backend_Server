import io
from unittest.mock import MagicMock

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.services.face_service import FaceResult


def _make_fake_embedding(dim=512):
    emb = np.random.randn(dim).astype(np.float32)
    emb /= np.linalg.norm(emb)
    return emb


def _fake_detect_and_embed_single(image, conf_threshold=0.5):
    return [FaceResult(bbox=[10, 20, 100, 100], embedding=_make_fake_embedding(), confidence=0.95)]


def _fake_detect_and_embed_none(image, conf_threshold=0.5):
    return []


def _fake_detect_and_embed_multi(image, conf_threshold=0.5):
    return [
        FaceResult(bbox=[10, 20, 100, 100], embedding=_make_fake_embedding(), confidence=0.95),
        FaceResult(bbox=[110, 20, 100, 100], embedding=_make_fake_embedding(), confidence=0.90),
    ]


def _png_bytes():
    import struct
    import zlib

    width, height = 1, 1
    raw = b"\x00\x00\x00" * (width * height)
    filtered = b"\x00" + raw
    compressed = zlib.compress(filtered)

    def chunk(ctype, data):
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    return png


def _make_mock_face_service(detect_side_effect=None):
    from app.services.face_service import FaceRecognitionService

    svc = MagicMock(spec=FaceRecognitionService)
    svc._initialized = True
    if detect_side_effect:
        svc.detect_and_embed = MagicMock(side_effect=detect_side_effect)
    else:
        svc.detect_and_embed = MagicMock(side_effect=_fake_detect_and_embed_single)
    svc.average_embeddings = MagicMock(side_effect=lambda embs: FaceRecognitionService.average_embeddings(embs))
    return svc


@pytest.fixture
def mock_face(client):
    svc = _make_mock_face_service()
    client.app.state.face_service = svc
    yield svc
    if hasattr(client.app.state, "face_service"):
        del client.app.state.face_service


def test_register_no_photos(client, auth_headers):
    resp = client.post(
        "/api/v1/employees/register",
        headers=auth_headers,
        data={"username": "user1"},
    )
    assert resp.status_code == 422


def test_register_single_photo(client, auth_headers, mock_face):
    png = _png_bytes()
    files = [("files", ("photo.png", io.BytesIO(png), "image/png"))]
    resp = client.post(
        "/api/v1/employees/register",
        headers=auth_headers,
        data={"username": "user_single"},
        files=files,
    )
    assert resp.status_code == 400
    assert "Exactly 3" in resp.json()["detail"]


def test_register_wrong_photo_count(client, auth_headers):
    png = _png_bytes()
    files = [("files", (f"photo{i}.png", io.BytesIO(png), "image/png")) for i in range(4)]
    resp = client.post(
        "/api/v1/employees/register",
        headers=auth_headers,
        data={"username": "user1"},
        files=files,
    )
    assert resp.status_code == 400
    assert "Exactly 3" in resp.json()["detail"]


def test_register_success_3_photos(client, auth_headers, mock_face):
    png = _png_bytes()
    files = [("files", (f"photo{i}.png", io.BytesIO(png), "image/png")) for i in range(3)]
    resp = client.post(
        "/api/v1/employees/register",
        headers=auth_headers,
        data={"username": "user1"},
        files=files,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "user1"
    assert mock_face.detect_and_embed.call_count == 3





def test_register_no_face_in_photo(client, auth_headers):
    call_count = [0]

    def side_effect_no_face(image, conf_threshold=0.5):
        call_count[0] += 1
        if call_count[0] == 2:
            return []
        return _fake_detect_and_embed_single(image, conf_threshold)

    mock_svc = _make_mock_face_service(detect_side_effect=side_effect_no_face)
    client.app.state.face_service = mock_svc
    try:
        png = _png_bytes()
        files = [("files", (f"photo{i}.png", io.BytesIO(png), "image/png")) for i in range(3)]
        resp = client.post(
            "/api/v1/employees/register",
            headers=auth_headers,
            data={"username": "user1"},
            files=files,
        )
        assert resp.status_code == 400
        assert "No face detected in file 2" in resp.json()["detail"]
    finally:
        del client.app.state.face_service


def test_register_multiple_faces(client, auth_headers):
    call_count = [0]

    def side_effect_multi(image, conf_threshold=0.5):
        call_count[0] += 1
        if call_count[0] == 3:
            return _fake_detect_and_embed_multi(image, conf_threshold)
        return _fake_detect_and_embed_single(image, conf_threshold)

    mock_svc = _make_mock_face_service(detect_side_effect=side_effect_multi)
    client.app.state.face_service = mock_svc
    try:
        png = _png_bytes()
        files = [("files", (f"photo{i}.png", io.BytesIO(png), "image/png")) for i in range(3)]
        resp = client.post(
            "/api/v1/employees/register",
            headers=auth_headers,
            data={"username": "user1"},
            files=files,
        )
        assert resp.status_code == 400
        assert "Multiple faces" in resp.json()["detail"]
    finally:
        del client.app.state.face_service


def test_register_unauthorized(client):
    png = _png_bytes()
    files = [("files", ("photo.png", io.BytesIO(png), "image/png"))]
    resp = client.post(
        "/api/v1/employees/register",
        data={"username": "user1"},
        files=files,
    )
    assert resp.status_code == 401


def test_re_embed_success(client, auth_headers, mock_face):
    png = _png_bytes()
    files_reg = [("files", (f"photo{i}.png", io.BytesIO(png), "image/png")) for i in range(3)]
    reg_resp = client.post(
        "/api/v1/employees/register",
        headers=auth_headers,
        data={"username": "user_reembed"},
        files=files_reg,
    )
    assert reg_resp.status_code == 200
    emp_id = reg_resp.json()["id"]

    files_re = [("files", (f"photo{i}.png", io.BytesIO(png), "image/png")) for i in range(3)]
    re_resp = client.post(
        f"/api/v1/employees/{emp_id}/re-embed",
        headers=auth_headers,
        files=files_re,
    )
    assert re_resp.status_code == 200
    assert re_resp.json()["id"] == emp_id


def test_re_embed_single_photo(client, auth_headers, mock_face):
    png = _png_bytes()
    files_reg = [("files", (f"photo{i}.png", io.BytesIO(png), "image/png")) for i in range(3)]
    reg_resp = client.post(
        "/api/v1/employees/register",
        headers=auth_headers,
        data={"username": "user_reembed_single"},
        files=files_reg,
    )
    assert reg_resp.status_code == 200
    emp_id = reg_resp.json()["id"]

    files_re = [("files", (f"photo{i}.png", io.BytesIO(png), "image/png")) for i in range(3)]
    re_resp = client.post(
        f"/api/v1/employees/{emp_id}/re-embed",
        headers=auth_headers,
        files=files_re,
    )
    assert re_resp.status_code == 200
    assert mock_face.detect_and_embed.call_count == 6  # 3 register + 3 re-embed


def test_re_embed_employee_not_found(client, auth_headers, mock_face):
    png = _png_bytes()
    files = [("files", (f"photo{i}.png", io.BytesIO(png), "image/png")) for i in range(3)]
    resp = client.post(
        "/api/v1/employees/9999/re-embed",
        headers=auth_headers,
        files=files,
    )
    assert resp.status_code == 404


def test_re_embed_too_few_photos(client, auth_headers, mock_face):
    resp = client.post(
        "/api/v1/employees/1/re-embed",
        headers=auth_headers,
    )
    assert resp.status_code == 422