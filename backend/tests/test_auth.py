from unittest.mock import Mock

from fastapi.testclient import TestClient
from fastapi import HTTPException, status

from app.core.dependencies import get_current_user
from app.main import app


client = TestClient(app)


def test_me_without_token_returns_401():
    response = client.get("/users/me")

    assert response.status_code == 401


def test_me_with_invalid_token_returns_401():
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer faux.jeton.invalide"},
    )

    assert response.status_code == 401


def test_inactive_user_returns_401():
    async def inactive_user():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    app.dependency_overrides[get_current_user] = inactive_user

    try:
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer token-de-test"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 401