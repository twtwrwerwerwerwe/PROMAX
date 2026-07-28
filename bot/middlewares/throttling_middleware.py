# -*- coding: utf-8 -*-
"""
bot/middlewares/throttling_middleware.py — Double-click / duplicate update himoyasi.

Bitta foydalanuvchidan bir xil turdagi update (message yoki callback)
juda qisqa vaqt oralig'ida qayta kelsa — takroriy so'rov sifatida
e'tiborsiz qoldiriladi. Bu tarmoq retry'lari, Telegram duplicate
update'lari va foydalanuvchi tugmani ikki marta bosishidan himoya qiladi.
"""
from __future__ import annotations

import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

_DEFAULT_WINDOW_SECONDS = 0.7


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, window_seconds: float = _DEFAULT_WINDOW_SECONDS):
        self._window = window_seconds
        self._last_seen: Dict[str, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        key = self._build_key(event)
        if key is not None:
            now = time.monotonic()
            last = self._last_seen.get(key)
            if last is not None and (now - last) < self._window:
                if isinstance(event, CallbackQuery):
                    await event.answer()
                return None
            self._last_seen[key] = now
            # Cache accumulation cheklash — eski yozuvlarni davriy tozalash.
            if len(self._last_seen) > 5000:
                cutoff = now - 60
                self._last_seen = {k: v for k, v in self._last_seen.items() if v > cutoff}

        return await handler(event, data)

    @staticmethod
    def _build_key(event: TelegramObject) -> str | None:
        if isinstance(event, CallbackQuery):
            return f"cb:{event.from_user.id}:{event.data}"
        if isinstance(event, Message):
            content = event.text or event.caption or (event.contact.phone_number if event.contact else "") or str(event.message_id)
            return f"msg:{event.from_user.id}:{content}"
        return None
