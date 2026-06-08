from fastapi.testclient import TestClient

from app.services.token_service import TokenService


def test_admin_login_unregistered(client: TestClient):
    response = client.post(
        "/api/v1/admins/login",
        json={"username": "nonexistent", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_admin_register_with_env_invite_code(client: TestClient, db):
    from app.services.invite_service import InviteService

    invite = InviteService.create_invite_code(db, created_by=None)

    response = client.post(
        "/api/v1/admins/register",
        json={
            "username": "newadmin",
            "email": "newadmin@example.com",
            "password": "securepassword123",
            "invite_code": invite.code,
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


def test_forgot_password_existing_user(client: TestClient, test_admin):
    response = client.post(
        "/api/v1/admins/forgot-password",
        json={"username": "testadmin"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "If the account exists, a reset email has been sent"


def test_forgot_password_by_email(client: TestClient, test_admin):
    response = client.post(
        "/api/v1/admins/forgot-password",
        json={"username": "testadmin@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "If the account exists, a reset email has been sent"


def test_forgot_password_rate_limited(client: TestClient, test_admin, db):
    from app.models import PasswordResetToken

    response1 = client.post(
        "/api/v1/admins/forgot-password",
        json={"username": "testadmin"},
    )
    assert response1.status_code == 200

    tokens_after_first = db.query(PasswordResetToken).filter(
        PasswordResetToken.admin_id == test_admin.id,
    ).count()

    response2 = client.post(
        "/api/v1/admins/forgot-password",
        json={"username": "testadmin"},
    )
    assert response2.status_code == 200

    tokens_after_second = db.query(PasswordResetToken).filter(
        PasswordResetToken.admin_id == test_admin.id,
    ).count()
    assert tokens_after_second == tokens_after_first


def test_forgot_password_nonexistent_user(client: TestClient):
    response = client.post(
        "/api/v1/admins/forgot-password",
        json={"username": "nonexistent"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "If the account exists, a reset email has been sent"


def test_reset_password_with_valid_token(client: TestClient, test_admin, db):
    token = TokenService.generate_reset_token(test_admin.id, db)

    response = client.post(
        "/api/v1/admins/reset-password",
        json={"token": token, "new_password": "newpassword456"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully"

    login_response = client.post(
        "/api/v1/admins/login",
        json={"username": "testadmin", "password": "newpassword456"},
    )
    assert login_response.status_code == 200


def test_reset_password_with_invalid_token(client: TestClient):
    response = client.post(
        "/api/v1/admins/reset-password",
        json={"token": "invalid1", "new_password": "newpassword456"},
    )
    assert response.status_code == 400
    assert "Invalid or expired token" in response.json()["detail"]


def test_reset_password_token_single_use(client: TestClient, test_admin, db):
    token = TokenService.generate_reset_token(test_admin.id, db)

    response1 = client.post(
        "/api/v1/admins/reset-password",
        json={"token": token, "new_password": "newpassword456"},
    )
    assert response1.status_code == 200

    response2 = client.post(
        "/api/v1/admins/reset-password",
        json={"token": token, "new_password": "anotherpassword789"},
    )
    assert response2.status_code == 400


def test_verify_reset_token_valid(client: TestClient, test_admin, db):
    token = TokenService.generate_reset_token(test_admin.id, db)

    response = client.post(
        "/api/v1/admins/verify-reset-token",
        json={"token": token},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True


def test_verify_reset_token_invalid(client: TestClient):
    response = client.post(
        "/api/v1/admins/verify-reset-token",
        json={"token": "invalid1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False