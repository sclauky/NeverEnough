from datetime import timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.product import Product
from app.models.product_price import ProductPrice
from app.models.store import Store
from app.models.user import User
from app.schemas.product_price import ProductPriceCreate, ProductPricePublic


router = APIRouter(
    prefix="/prices",
    tags=["Product prices"],
)


@router.get(
    "",
    response_model=list[ProductPricePublic],
)
async def list_product_prices(
    product_id: UUID | None = None,
    store_id: UUID | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(ProductPrice)

    if product_id is not None:
        query = query.where(ProductPrice.product_id == product_id)

    if store_id is not None:
        query = query.where(ProductPrice.store_id == store_id)

    result = await session.scalars(
        query
        .order_by(
            ProductPrice.observed_at.desc(),
            ProductPrice.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return result.all()


@router.get(
    "/latest",
    response_model=list[ProductPricePublic],
)
async def get_latest_product_prices(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    latest_prices = (
        select(
            ProductPrice.id.label("price_id"),
            func.row_number()
            .over(
                partition_by=ProductPrice.store_id,
                order_by=(
                    ProductPrice.observed_at.desc(),
                    ProductPrice.created_at.desc(),
                ),
            )
            .label("row_number"),
        )
        .where(ProductPrice.product_id == product_id)
        .subquery()
    )

    result = await session.scalars(
        select(ProductPrice)
        .join(
            latest_prices,
            ProductPrice.id == latest_prices.c.price_id,
        )
        .where(latest_prices.c.row_number == 1)
        .order_by(ProductPrice.price)
    )

    return result.all()


@router.get(
    "/{price_id}",
    response_model=ProductPricePublic,
)
async def get_product_price(
    price_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    product_price = await session.get(ProductPrice, price_id)

    if product_price is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product price not found.",
        )

    return product_price


@router.post(
    "",
    response_model=ProductPricePublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_product_price(
    price_data: ProductPriceCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if (
        price_data.observed_at.tzinfo is None
        or price_data.observed_at.utcoffset() is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="observed_at must include a timezone.",
        )

    product = await session.get(Product, price_data.product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    store = await session.get(Store, price_data.store_id)

    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found.",
        )

    product_price = ProductPrice(
        **price_data.model_dump(),
        observed_at=price_data.observed_at.astimezone(timezone.utc),
    )

    session.add(product_price)
    await session.commit()
    await session.refresh(product_price)

    return product_price