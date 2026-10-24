
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings


def create_access_token(subject: str) -> str:
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured.")

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured.")

    return jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
