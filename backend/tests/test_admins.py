from fastapi.testclient import TestClient


def test_admin_login_unregistered(client: TestClient):
    response = client.post(
        "/api/v1/admins/login",
        json={"username": "nonexistent", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_admin_register_with_env_invite_code(client: TestClient, db):
    response = client.post(
        "/api/v1/admins/register",
        json={
            "username": "newadmin",
            "email": "newadmin@example.com",
            "password": "securepassword123",
            "invite_code": "testinvitecode1234",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newadmin"
    assert data["email"] == "newadmin@example.com"


def test_admin_login_success(client: TestClient, test_admin):
    response = client.post(
        "/api/v1/admins/login",
        json={"username": "testadmin", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_admin_me_authenticated(client: TestClient, auth_headers):
    response = client.get("/api/v1/admins/me", headers=auth_headers)
    assert response.status_code == 200