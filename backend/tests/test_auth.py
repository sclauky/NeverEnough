from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import get_current_user
from app.core.tokens import create_access_token


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