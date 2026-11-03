
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.api.routes.users import (
    get_current_user_preferences,
    update_current_user_preferences,
)
from app.schemas.user_preferences import UserPreferencesUpdate


def make_result(value=None, values=None):
    return SimpleNamespace(
        scalar_one_or_none=lambda: value,
        scalars=lambda: SimpleNamespace(
            all=lambda: values or []
        ),
    )


def make_session(results):
    return SimpleNamespace(
        execute=AsyncMock(side_effect=results),
        flush=AsyncMock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
        add=MagicMock(),
        add_all=MagicMock(),
    )


@pytest.mark.asyncio
async def test_get_preferences_without_existing_preferences():
    user = SimpleNamespace(id=uuid4())
    session = make_session([make_result(value=None)])

    result = await get_current_user_preferences(
        current_user=user,
        session=session,
    )

    assert result.dietary_preferences == []
    assert result.allergies == []
    assert result.kitchen_equipment == []


@pytest.mark.asyncio
async def test_get_existing_preferences():
    user = SimpleNamespace(id=uuid4())
    preferences = SimpleNamespace(id=uuid4())

    session = make_session([
        make_result(value=preferences),
        make_result(values=["vegetarian"]),
        make_result(values=["peanuts", "milk"]),
        make_result(values=["oven", "microwave"]),
    ])

    result = await get_current_user_preferences(
        current_user=user,
        session=session,
    )

    assert result.dietary_preferences == ["vegetarian"]
    assert result.allergies == ["peanuts", "milk"]
    assert result.kitchen_equipment == ["oven", "microwave"]


@pytest.mark.asyncio
async def test_update_preferences_success():
    user = SimpleNamespace(id=uuid4())
    preferences = SimpleNamespace(id=uuid4())

    session = make_session([
        make_result(value=preferences),
        make_result(),
        make_result(),
        make_result(),
    ])

    data = UserPreferencesUpdate(
        dietary_preferences=["vegetarian"],
        allergies=["peanuts"],
        kitchen_equipment=["oven", "air_fryer"],
    )

    result = await update_current_user_preferences(
        data=data,
        current_user=user,
        session=session,
    )

    assert result.dietary_preferences == ["vegetarian"]
    assert result.allergies == ["peanuts"]
    assert result.kitchen_equipment == ["oven", "air_fryer"]

    assert session.execute.await_count == 4
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()
    assert session.add_all.call_count == 3


@pytest.mark.asyncio
async def test_update_creates_preferences_if_missing():
    user = SimpleNamespace(id=uuid4())

    session = make_session([
        make_result(value=None),
        make_result(),
        make_result(),
        make_result(),
    ])

    data = UserPreferencesUpdate(
        dietary_preferences=["vegan"],
        allergies=[],
        kitchen_equipment=["stovetop"],
    )

    result = await update_current_user_preferences(
        data=data,
        current_user=user,
        session=session,
    )

    assert result.dietary_preferences == ["vegan"]
    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_rolls_back_on_database_error():
    user = SimpleNamespace(id=uuid4())
    preferences = SimpleNamespace(id=uuid4())

    session = make_session([
        make_result(value=preferences),
        make_result(),
        make_result(),
        make_result(),
    ])
    session.commit.side_effect = RuntimeError("Database error")

    data = UserPreferencesUpdate(
        dietary_preferences=["vegetarian"],
        allergies=[],
        kitchen_equipment=[],
    )

    with pytest.raises(RuntimeError):
        await update_current_user_preferences(
            data=data,
            current_user=user,
            session=session,
        )

    session.rollback.assert_awaited_once()


def test_preferences_reject_invalid_dietary_preference():
    with pytest.raises(ValueError):
        UserPreferencesUpdate(
            dietary_preferences=["invalid"],
            allergies=[],
            kitchen_equipment=[],
        )


def test_preferences_reject_invalid_allergy():
    with pytest.raises(ValueError):
        UserPreferencesUpdate(
            dietary_preferences=[],
            allergies=["invalid"],
            kitchen_equipment=[],
        )


def test_preferences_reject_invalid_equipment():
    with pytest.raises(ValueError):
        UserPreferencesUpdate(
            dietary_preferences=[],
            allergies=[],
            kitchen_equipment=["invalid"],
        )


def test_preferences_reject_duplicates():
    with pytest.raises(ValueError):
        UserPreferencesUpdate(
            dietary_preferences=["vegetarian", "vegetarian"],
            allergies=[],
            kitchen_equipment=[],
        )


def test_preferences_reject_unknown_fields():
    with pytest.raises(ValueError):
        UserPreferencesUpdate(
            dietary_preferences=[],
            allergies=[],
            kitchen_equipment=[],
            unknown_field="value",
        )