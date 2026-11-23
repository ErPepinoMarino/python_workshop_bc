from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from integrated_app.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_settings().database_url,
            pool_pre_ping=True,
        )
    return _engine


async def close_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    session_maker = async_sessionmaker(get_engine(), expire_on_commit=False)
    async with session_maker() as session:
        async with session.begin():
            yield session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session_maker = async_sessionmaker(get_engine(), expire_on_commit=False)
    async with session_maker() as session:
        async with session.begin():
            yield session
