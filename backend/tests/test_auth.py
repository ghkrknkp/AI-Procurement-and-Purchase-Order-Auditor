import pytest
from app.models import UserRole

def test_register_user_defaults_to_submitter(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "SecurePassword123!"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "jane@example.com"
    assert data["role"] == UserRole.SUBMITTER.value

def test_login_success(client, test_submitter):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_submitter.email,
            "password": "Password123!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" == data["token_type"] or "bearer" in data["token_type"].lower()
    assert data["user"]["email"] == test_submitter.email

def test_login_invalid_password(client, test_submitter):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_submitter.email,
            "password": "WrongPassword!"
        }
    )
    assert response.status_code == 401

def test_get_me(client, submitter_token):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {submitter_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test_sub@edvexa.com"
    assert data["role"] == "submitter"

def test_unauthenticated_request_fails(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
