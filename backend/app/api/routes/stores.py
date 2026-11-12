from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.store import Store
from app.models.user import User
from app.schemas.store import StoreCreate, StorePublic


router = APIRouter(
    prefix="/stores",
    tags=["Stores"],
)


@router.get(
    "",
    response_model=list[StorePublic],
)
async def list_stores(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.scalars(
        select(Store)
        .order_by(Store.chain_name, Store.city, Store.name)
        .offset(offset)
        .limit(limit)
    )

    return result.all()


@router.get(
    "/{store_id}",
    response_model=StorePublic,
)
async def get_store(
    store_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    store = await session.get(Store, store_id)

    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found.",
        )

    return store


@router.post(
    "",
    response_model=StorePublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_store(
    store_data: StoreCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    existing_store = await session.scalar(
        select(Store).where(
            Store.chain_name == store_data.chain_name,
            Store.name == store_data.name,
            Store.address == store_data.address,
            Store.postal_code == store_data.postal_code,
            Store.city == store_data.city,
            Store.country_code == store_data.country_code,
        )
    )

    if existing_store is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This store already exists.",
        )

    store = Store(**store_data.model_dump())

    session.add(store)
    await session.commit()
    await session.refresh(store)

    return store