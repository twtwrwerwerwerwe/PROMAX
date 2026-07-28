# -*- coding: utf-8 -*-
"""bot/middlewares/db_middleware.py — Har bir update uchun DB session va servislarni inject qiladi."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.core.containers import ServiceContainer
from bot.database.engine import get_session


class DatabaseMiddleware(BaseMiddleware):
    """Har bir update uchun bitta tranzaksion session ochadi.

    Handler muvaffaqiyatli tugasa — commit, xatolik bo'lsa — rollback
    avtomatik ravishda `get_session()` context manager ichida bajariladi.
    """

    def __init__(self, bot):
        self.bot = bot

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with get_session() as session:
            data["services"] = ServiceContainer.build(session, self.bot)
            return await handler(event, data)
