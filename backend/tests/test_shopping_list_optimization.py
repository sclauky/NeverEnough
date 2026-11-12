from decimal import Decimal
from uuid import uuid4

from app.services.shopping_list_optimization import (
    build_shopping_selection,
)


def make_candidate(
    product_id,
    package_quantity,
    package_price,
    store_id,
    store_name,
):
    return {
        "product_id": product_id,
        "product_name": "Pâtes",
        "brand": "Test",
        "package_quantity": package_quantity,
        "package_unit": "g",
        "package_price": package_price,
        "currency_code": "EUR",
        "unit_price": package_price / package_quantity,
        "package_base_quantity": package_quantity,
        "_store_id": str(store_id),
        "_store_name": store_name,
        "_chain_name": store_name,
    }


def test_consumed_optimization_selects_lowest_unit_price():
    ingredient_id = uuid4()
    store_id = uuid4()

    products = {
        ingredient_id: [
            make_candidate(
                uuid4(),
                Decimal("1000"),
                Decimal("2.00"),
                store_id,
                "Store A",
            ),
            make_candidate(
                uuid4(),
                Decimal("250"),
                Decimal("0.60"),
                store_id,
                "Store A",
            ),
        ]
    }

    ingredient_totals = {
        ingredient_id: {
            "quantity": Decimal("300"),
            "unit": "g",
        }
    }

    result = build_shopping_selection(
        ingredient_totals,
        products,
        "consumed",
    )

    assert result["complete"] is True
    assert result["total"] == Decimal("0.60")
    assert result["items"][0]["packages_needed"] == 1
    assert result["items"][0]["store_name"] == "Store A"


def test_purchase_optimization_selects_lowest_package_cost():
    ingredient_id = uuid4()
    store_id = uuid4()

    products = {
        ingredient_id: [
            make_candidate(
                uuid4(),
                Decimal("1000"),
                Decimal("2.00"),
                store_id,
                "Store A",
            ),
            make_candidate(
                uuid4(),
                Decimal("250"),
                Decimal("0.60"),
                store_id,
                "Store A",
            ),
        ]
    }

    ingredient_totals = {
        ingredient_id: {
            "quantity": Decimal("300"),
            "unit": "g",
        }
    }

    result = build_shopping_selection(
        ingredient_totals,
        products,
        "purchase",
    )

    assert result["complete"] is True
    assert result["total"] == Decimal("1.20")
    assert result["items"][0]["packages_needed"] == 2
    assert result["items"][0]["store_name"] == "Store A"


def test_selection_reports_missing_ingredients():
    ingredient_id = uuid4()

    ingredient_totals = {
        ingredient_id: {
            "quantity": Decimal("300"),
            "unit": "g",
        }
    }

    result = build_shopping_selection(
        ingredient_totals,
        {},
        "consumed",
    )

    assert result["complete"] is False
    assert result["missing_ingredients"] == [str(ingredient_id)]
    assert result["items"] == []