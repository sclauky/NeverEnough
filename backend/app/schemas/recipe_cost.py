from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RecipeCostItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ingredient_id: UUID
    product_id: UUID
    product_name: str
    brand: str | None
    required_quantity: Decimal
    unit: str
    packages_needed: int
    package_quantity: Decimal
    package_unit: str
    package_price: Decimal
    consumed_cost: Decimal
    purchase_cost: Decimal
    currency_code: str


class RecipeCostOptimization(BaseModel):
    model_config = ConfigDict(extra="forbid")

    complete: bool
    missing_ingredients: list[UUID]
    total: Decimal
    currency_code: str
    items: list[RecipeCostItem]


class MissingRecipeIngredient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ingredient_id: UUID
    ingredient_name: str
    reason: Literal[
        "Missing quantity or unit.",
        "Unsupported recipe unit.",
        "Incompatible units for the same ingredient.",
    ]


class RecipeCostStore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    store_id: UUID
    store_name: str
    chain_name: str
    address: str
    city: str
    consumed_optimization: RecipeCostOptimization
    purchase_optimization: RecipeCostOptimization


class RecipeCostPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: UUID
    recipe_title: str
    servings: int
    stores: list[RecipeCostStore]
    missing_ingredients: list[MissingRecipeIngredient]