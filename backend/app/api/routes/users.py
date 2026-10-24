
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserCreate, UserMe


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