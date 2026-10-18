from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine: # check if db is well configured
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL n'est pas configurée."
        )

    url = make_url(settings.database_url)

    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")
    elif url.drivername != "postgresql+asyncpg":
        raise RuntimeError(
            "Never Enough nécessite une URL PostgreSQL compatible asyncpg."
        )

    return create_async_engine(
        url,
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1) # create only once 
def get_session_factory() -> async_sessionmaker[AsyncSession]: # preparing sessions
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
    )


async def get_session() -> AsyncIterator[AsyncSession]: # session x backend opération 
    async with get_session_factory()() as session:
        yield session