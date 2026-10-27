from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.meal_plan import MealPlanCreate
from app.schemas.recipe import RecipeCreate
from app.schemas.recipe_ingredient import RecipeIngredientCreate
from app.schemas.user import UserCreate
from app.schemas.user_budget import UserBudgetCreate


def test_user_create_accepts_valid_data():
    user = UserCreate(
        email="alex@example.com",
        username="alex_01",
        password="UnePhraseDePasseTresLongue123!",
    )

    assert user.email == "alex@example.com"
    assert user.username == "alex_01"


def test_user_create_rejects_short_password():
    with pytest.raises(ValidationError):
        UserCreate(
            email="alex@example.com",
            username="alex_01",
            password="court",
        )


def test_recipe_create_uses_default_servings():
    recipe = RecipeCreate(title="Pâtes à la tomate")

    assert recipe.servings == 2
    assert recipe.description is None


def test_recipe_create_rejects_empty_title():
    with pytest.raises(ValidationError):
        RecipeCreate(title="   ")


def test_recipe_ingredient_rejects_zero_quantity():
    with pytest.raises(ValidationError):
        RecipeIngredientCreate(
            ingredient_id=uuid4(),
            quantity="0",
            unit="g",
        )


def test_user_budget_accepts_weekly_budget():
    budget = UserBudgetCreate(
        amount="50.00",
        period_type="week",
    )

    assert budget.period_type == "week"
    assert budget.amount == 50


def test_user_budget_rejects_invalid_period():
    with pytest.raises(ValidationError):
        UserBudgetCreate(
            amount="50.00",
            period_type="year",
        )


def test_meal_plan_rejects_invalid_date_range():
    with pytest.raises(ValidationError):
        MealPlanCreate(
            start_date=date(2026, 10, 25),
            end_date=date(2026, 10, 20),
        )