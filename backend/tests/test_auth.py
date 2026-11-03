
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.routes.users import update_current_user_password
from app.core.dependencies import get_current_user
from app.core.security import hash_password, verify_password
from app.core.tokens import create_access_token
from app.schemas.user import UserPasswordUpdate


@pytest.mark.asyncio
async def test_inactive_user_returns_401():
    user_id = uuid4()

    inactive_user = SimpleNamespace(
        id=user_id,
        is_active=False,
    )

    session = SimpleNamespace(
        scalar=AsyncMock(return_value=inactive_user),
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=create_access_token(str(user_id)),
    )

    with pytest.raises(HTTPException) as exception:
        await get_current_user(
            credentials=credentials,
            session=session,
        )

    assert exception.value.status_code == 401


@pytest.mark.asyncio
async def test_password_update_success():
    current_user = SimpleNamespace(
        password_hash=hash_password("OldPassword123!"),
    )
    session = SimpleNamespace(commit=AsyncMock())

    password_data = UserPasswordUpdate(
        current_password="OldPassword123!",
        new_password="NewPassword456!",
        confirm_new_password="NewPassword456!",
    )

    result = await update_current_user_password(
        password_data=password_data,
        current_user=current_user,
        session=session,
    )

    assert verify_password("NewPassword456!", current_user.password_hash)
    assert not verify_password("OldPassword123!", current_user.password_hash)
    session.commit.assert_awaited_once()
    assert result["message"] == "Your password has been successfully updated."


@pytest.mark.asyncio
async def test_password_update_rejects_wrong_current_password():
    current_user = SimpleNamespace(
        password_hash=hash_password("OldPassword123!"),
    )
    session = SimpleNamespace(commit=AsyncMock())

    password_data = UserPasswordUpdate(
        current_password="WrongPassword123!",
        new_password="NewPassword456!",
        confirm_new_password="NewPassword456!",
    )

    with pytest.raises(HTTPException) as exception:
        await update_current_user_password(
            password_data=password_data,
            current_user=current_user,
            session=session,
        )

    assert exception.value.status_code == 400
    session.commit.assert_not_awaited()


def test_password_update_rejects_mismatched_passwords():
    with pytest.raises(ValueError):
        UserPasswordUpdate(
            current_password="OldPassword123!",
            new_password="NewPassword456!",
            confirm_new_password="DifferentPassword789!",
        )


def test_password_update_rejects_same_password():
    with pytest.raises(ValueError):
        UserPasswordUpdate(
            current_password="OldPassword123!",
            new_password="OldPassword123!",
            confirm_new_password="OldPassword123!",
        )