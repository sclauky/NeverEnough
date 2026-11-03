import hmac
import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.email import send_email
from app.core.email_tokens import (
    generate_email_change_token,
    get_email_change_expiration,
    hash_email_change_token,
    is_email_change_token_expired,
)
from app.core.security import hash_password, verify_password
from app.core.tokens import create_access_token
from app.db.session import get_session
from app.models.email_change_request import EmailChangeRequest
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserEmailUpdate,
    UserLogin,
    UserMe,
    TokenResponse,
    UserPasswordUpdate,
    UserPublic,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserMe,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> User:
    email = user_data.email.lower()

    existing_user = await session.scalar(
        select(User).where(
            (User.email == email)
            | (User.username == user_data.username)
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already exists.",
        )

    user = User(
        id=uuid.uuid4(),
        email=email,
        username=user_data.username,
        password_hash=hash_password(user_data.password),
    )

    session.add(user)

    try:
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already exists.",
        )

    return user


@router.post("/login", response_model=TokenResponse)
async def login_user(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    email = credentials.email.lower()

    user = await session.scalar(
        select(User).where(User.email == email)
    )

    if user is None or not verify_password(
        credentials.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    access_token = create_access_token(str(user.id))

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserPublic)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.patch("/me", response_model=UserPublic)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    updates = user_data.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No changes provided.",
        )

    if "username" in updates:
        existing_user = await session.scalar(
            select(User).where(
                User.username == updates["username"],
                User.id != current_user.id,
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists.",
            )

        current_user.username = updates["username"]

    try:
        await session.commit()
        await session.refresh(current_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists.",
        )

    return current_user


@router.patch("/me/password")
async def update_current_user_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not verify_password(
        password_data.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    current_user.password_hash = hash_password(
        password_data.new_password
    )

    await session.commit()

    return {
        "message": "Your password has been successfully updated."
    }

@router.post("/me/email/change-request")
async def request_email_change(
    email_data: UserEmailUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    new_email = str(email_data.email).lower()

    if new_email == current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This is already your email address.",
        )

    existing_user = await session.scalar(
        select(User).where(User.email == new_email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists.",
        )

    await session.execute(
        delete(EmailChangeRequest).where(
            EmailChangeRequest.user_id == current_user.id
        )
    )

    token, token_hash = generate_email_change_token()

    email_request = EmailChangeRequest(
        user_id=current_user.id,
        new_email=new_email,
        token_hash=token_hash,
        expires_at=get_email_change_expiration(),
    )

    session.add(email_request)
    await session.commit()

    confirmation_url = (
        f"{settings.frontend_url.rstrip('/')}"
        f"/confirm-email?token={token}"
    )

    try:
        await send_email(
            recipient=new_email,
            subject="Never Enough - Confirm your email change",
            body=(
                "You requested to change your Never Enough email address.\n\n"
                f"Confirm your new email address using this link:\n"
                f"{confirmation_url}\n\n"
                "This link expires in 30 minutes.\n\n"
                "If you did not request this change, ignore this email."
            ),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send the confirmation email. Please try again.",
        )

    return {
        "message": "A confirmation email has been sent to your new address."
    }


@router.post("/me/email/confirm")
async def confirm_email_change(
    token: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
) -> dict:
    token_hash = hash_email_change_token(token)

    email_request = await session.scalar(
        select(EmailChangeRequest).where(
            EmailChangeRequest.token_hash == token_hash,
        )
    )

    if email_request is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation token.",
        )

    if is_email_change_token_expired(email_request.expires_at):
        await session.delete(email_request)
        await session.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation token has expired.",
        )

    user = await session.scalar(
        select(User).where(User.id == email_request.user_id)
    )

    if user is None:
        await session.delete(email_request)
        await session.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation request.",
        )

    existing_user = await session.scalar(
        select(User).where(
            User.email == email_request.new_email,
            User.id != user.id,
        )
    )

    if existing_user:
        await session.delete(email_request)
        await session.commit()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists.",
        )

    user.email = email_request.new_email
    await session.delete(email_request)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists.",
        )

    return {
        "message": "Your email address has been successfully updated."
    }