
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tokens import decode_access_token
from app.db.session import get_session
from app.models.user import User


bearer_scheme = HTTPBearer(
    scheme_name="JWT",
    auto_error=False,
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")

        if not isinstance(subject, str):
            raise credentials_exception

        user_id = UUID(subject)

    except (InvalidTokenError, ValueError):
        raise credentials_exception

    user = await session.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None or not user.is_active:
        raise credentials_exception

    return user