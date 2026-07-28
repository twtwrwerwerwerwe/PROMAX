# -*- coding: utf-8 -*-
"""bot/middlewares/banned_user_middleware.py — Bloklangan foydalanuvchilarni to'xtatadi."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.core.containers import ServiceContainer
from bot.utils.text_templates import T


class BannedUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        services: ServiceContainer | None = data.get("services")
        user = getattr(event, "from_user", None)

        if services is not None and user is not None:
            if await services.users.is_banned(user.id):
                if isinstance(event, CallbackQuery):
                    await event.answer(T.USER_IS_BANNED_MSG, show_alert=True)
                elif isinstance(event, Message):
                    await event.answer(T.USER_IS_BANNED_MSG)
                return None

        return await handler(event, data)
