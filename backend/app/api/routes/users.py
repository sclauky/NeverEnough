import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.core.tokens import create_access_token
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserMe, TokenResponse

from app.core.dependencies import get_current_user
from app.schemas.user import UserPublic


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