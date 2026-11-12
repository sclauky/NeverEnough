from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ShoppingOptimizationItem(BaseModel):
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
    store_id: UUID
    store_name: str
    chain_name: str | None


class ShoppingOptimizationResult(BaseModel):
    complete: bool
    missing_ingredients: list[str]
    total: Decimal
    currency_code: str
    items: list[ShoppingOptimizationItem]


class ShoppingStoreOptimization(BaseModel):
    store_id: UUID
    store_name: str
    chain_name: str | None
    address: str | None
    city: str | None
    consumed_optimization: ShoppingOptimizationResult
    purchase_optimization: ShoppingOptimizationResult


class ShoppingUnpricedItem(BaseModel):
    item_id: UUID
    name: str
    reason: str


class ShoppingMultiStoreOptimization(BaseModel):
    consumed_optimization: ShoppingOptimizationResult | None
    purchase_optimization: ShoppingOptimizationResult | None


class ShoppingListOptimizationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shopping_list_id: UUID
    shopping_list_title: str | None
    stores: list[ShoppingStoreOptimization]
    multi_store_optimization: ShoppingMultiStoreOptimization
    unpriced_items: list[ShoppingUnpricedItem]