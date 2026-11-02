import hashlib
import secrets
from datetime import datetime, timedelta, timezone


EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES = 30


def generate_email_change_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return token, token_hash


def hash_email_change_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_email_change_expiration() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        minutes=EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES
    )


def is_email_change_token_expired(expires_at: datetime) -> bool:
    return datetime.now(timezone.utc) >= expires_at