from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.ingredient import Ingredient
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductPublic


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.get(
    "",
    response_model=list[ProductPublic],
)
async def list_products(
    search: str | None = Query(default=None, min_length=1, max_length=200),
    ingredient_id: UUID | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Product)

    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))

    if ingredient_id:
        query = query.where(Product.ingredient_id == ingredient_id)

    result = await session.scalars(
        query
        .order_by(Product.name)
        .offset(offset)
        .limit(limit)
    )

    return result.all()


@router.get(
    "/{product_id}",
    response_model=ProductPublic,
)
async def get_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    product = await session.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    return product


@router.post(
    "",
    response_model=ProductPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    product_data: ProductCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ingredient = await session.get(
        Ingredient,
        product_data.ingredient_id,
    )

    if ingredient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found.",
        )

    if product_data.barcode is not None:
        existing_product = await session.scalar(
            select(Product).where(
                Product.barcode == product_data.barcode
            )
        )

        if existing_product is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A product with this barcode already exists.",
            )

    product = Product(**product_data.model_dump())

    session.add(product)
    await session.commit()
    await session.refresh(product)

    return product