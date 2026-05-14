def test_singleton_identity(client):
    svc = client.app.state.face_service
    assert svc is not None, "face_service should be initialized in app.state"

    from app.deps import get_face_service

    dummy_request = type("Request", (), {"app": client.app})()
    svc_from_deps = get_face_service(dummy_request)
    assert svc_from_deps is svc, "get_face_service should return the same instance from app.state"