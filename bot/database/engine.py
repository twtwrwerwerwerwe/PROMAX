# -*- coding: utf-8 -*-
"""
bot/database/engine.py — Async SQLAlchemy engine va session factory.

Connection pooling shu yerda sozlanadi. Butun loyihada boshqa hech qanday
joyda `create_async_engine` chaqirilmaydi — bitta manba (single source of
truth).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Provides a transactional session as an async context manager.

    Commits on success, rolls back on any exception, always closes.
    """
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def dispose_engine() -> None:
    """Gracefully closes the connection pool. Call on shutdown."""
    await engine.dispose()
