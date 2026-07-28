# -*- coding: utf-8 -*-
"""bot/filters/admin_filter.py — Faqat ADMIN_IDS ro'yxatidagi foydalanuvchilarga ruxsat beruvchi filter."""
from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from bot.config import settings


class IsAdmin(BaseFilter):
    """Callback/Message yuboruvchi admin bo'lmasa — handler umuman ishga tushmaydi.

    Ruxsatsiz foydalanuvchiga admin menyu, admin callbacklari yoki
    admin handlerlarining mavjudligi haqida hech qanday ma'lumot
    berilmaydi (silent deny).
    """

    async def __call__(self, event: TelegramObject, *args, **kwargs) -> bool:
        user = getattr(event, "from_user", None)
        if user is None:
            return False
        return user.id in settings.admin_ids
