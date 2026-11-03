
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.routes.users import (
    get_current_user_budget,
    update_current_user_budget,
    delete_current_user_budget,
)
from app.schemas.user_budget import UserBudgetCreate


def make_result(value=None):
    return SimpleNamespace(
        scalar_one_or_none=lambda: value,
    )


def make_session(results):
    return SimpleNamespace(
        execute=AsyncMock(side_effect=results),
        commit=AsyncMock(),
        refresh=AsyncMock(),
        rollback=AsyncMock(),
        add=MagicMock(),
        delete=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_get_existing_budget():
    user = SimpleNamespace(id=uuid4())
    budget = SimpleNamespace(
        id=uuid4(),
        user_id=user.id,
        amount=Decimal("150.00"),
        period_type="month",
    )
    session = make_session([make_result(budget)])

    result = await get_current_user_budget(
        current_user=user,
        session=session,
    )

    assert result == budget


@pytest.mark.asyncio
async def test_get_missing_budget_returns_404():
    user = SimpleNamespace(id=uuid4())
    session = make_session([make_result(None)])

    with pytest.raises(HTTPException) as exception:
        await get_current_user_budget(
            current_user=user,
            session=session,
        )

    assert exception.value.status_code == 404


@pytest.mark.asyncio
async def test_create_budget():
    user = SimpleNamespace(id=uuid4())
    session = make_session([make_result(None)])

    data = UserBudgetCreate(
        amount=Decimal("150.00"),
        period_type="month",
    )

    result = await update_current_user_budget(
        data=data,
        current_user=user,
        session=session,
    )

    assert result.amount == Decimal("150.00")
    assert result.period_type == "month"
    assert result.user_id == user.id

    session.add.assert_called_once()
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update_existing_budget():
    user = SimpleNamespace(id=uuid4())
    budget = SimpleNamespace(
        id=uuid4(),
        user_id=user.id,
        amount=Decimal("150.00"),
        period_type="month",
    )
    session = make_session([make_result(budget)])

    data = UserBudgetCreate(
        amount=Decimal("200.00"),
        period_type="week",
    )

    result = await update_current_user_budget(
        data=data,
        current_user=user,
        session=session,
    )

    assert result.amount == Decimal("200.00")
    assert result.period_type == "week"

    session.add.assert_not_called()
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(budget)


@pytest.mark.asyncio
async def test_update_budget_rolls_back_on_error():
    user = SimpleNamespace(id=uuid4())
    session = make_session([make_result(None)])
    session.commit.side_effect = RuntimeError("Database error")

    data = UserBudgetCreate(
        amount=Decimal("150.00"),
        period_type="month",
    )

    with pytest.raises(RuntimeError):
        await update_current_user_budget(
            data=data,
            current_user=user,
            session=session,
        )

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_existing_budget():
    user = SimpleNamespace(id=uuid4())
    budget = SimpleNamespace(
        id=uuid4(),
        user_id=user.id,
        amount=Decimal("150.00"),
        period_type="month",
    )
    session = make_session([make_result(budget)])

    result = await delete_current_user_budget(
        current_user=user,
        session=session,
    )

    assert result is None
    session.delete.assert_awaited_once_with(budget)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_missing_budget_returns_404():
    user = SimpleNamespace(id=uuid4())
    session = make_session([make_result(None)])

    with pytest.raises(HTTPException) as exception:
        await delete_current_user_budget(
            current_user=user,
            session=session,
        )

    assert exception.value.status_code == 404
    session.delete.assert_not_awaited()
    session.commit.assert_not_awaited()


def test_budget_rejects_zero_amount():
    with pytest.raises(ValueError):
        UserBudgetCreate(
            amount=Decimal("0"),
            period_type="month",
        )


def test_budget_rejects_negative_amount():
    with pytest.raises(ValueError):
        UserBudgetCreate(
            amount=Decimal("-10"),
            period_type="month",
        )


def test_budget_rejects_invalid_period():
    with pytest.raises(ValueError):
        UserBudgetCreate(
            amount=Decimal("150"),
            period_type="year",
        )