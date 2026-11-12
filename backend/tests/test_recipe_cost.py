from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.recipe_cost import (
    build_selection,
    calculate_packages,
    convert_quantity,
)


@pytest.mark.parametrize(
    ("quantity", "source", "target", "expected"),
    [
        (Decimal("2"), "kg", "g", Decimal("2000")),
        (Decimal("1.5"), "l", "ml", Decimal("1500")),
        (Decimal("50"), "cl", "ml", Decimal("500")),
        (Decimal("250"), "mg", "g", Decimal("0.250")),
        (Decimal("3"), "pieces", "piece", Decimal("3")),
    ],
)
def test_convert_quantity(quantity, source, target, expected):
    assert convert_quantity(quantity, source, target) == expected


def test_convert_quantity_rejects_incompatible_units():
    assert convert_quantity(Decimal("1"), "kg", "ml") is None


@pytest.mark.parametrize(
    ("required", "package", "expected"),
    [
        (Decimal("300"), Decimal("1000"), 1),
        (Decimal("1200"), Decimal("500"), 3),
        (Decimal("1000"), Decimal("250"), 4),
    ],
)
def test_calculate_packages(required, package, expected):
    assert calculate_packages(required, package) == expected


def test_build_selection_optimizes_consumed_and_purchase_costs():
    ingredient_id = uuid4()

    ingredient_totals = {
        ingredient_id: {
            "quantity": Decimal("300"),
            "unit": "g",
            "name": "Pasta",
        }
    }

    products = {
        ingredient_id: [
            {
                "product_id": uuid4(),
                "product_name": "Pasta 1kg",
                "brand": None,
                "package_quantity": Decimal("1"),
                "package_unit": "kg",
                "package_price": Decimal("2.00"),
                "currency_code": "EUR",
                "unit_price": Decimal("0.002"),
                "package_base_quantity": Decimal("1000"),
            },
            {
                "product_id": uuid4(),
                "product_name": "Pasta 250g",
                "brand": None,
                "package_quantity": Decimal("250"),
                "package_unit": "g",
                "package_price": Decimal("0.60"),
                "currency_code": "EUR",
                "unit_price": Decimal("0.0024"),
                "package_base_quantity": Decimal("250"),
            },
        ]
    }

    consumed = build_selection(
        ingredient_totals,
        products,
        "consumed",
    )

    purchase = build_selection(
        ingredient_totals,
        products,
        "purchase",
    )

    assert consumed["items"][0]["product_name"] == "Pasta 1kg"
    assert consumed["total"] == Decimal("0.60")

    assert purchase["items"][0]["product_name"] == "Pasta 250g"
    assert purchase["total"] == Decimal("1.20")