# -*- coding: utf-8 -*-
"""bot/handlers/__init__.py — Barcha routerlarni yig'ib beruvchi asosiy funksiya."""
from aiogram import Router

from bot.handlers import group_events
from bot.handlers.admin import admin_router
from bot.handlers.user import user_router


def build_root_router() -> Router:
    """Barcha routerlarni to'g'ri tartibda bitta root routerga birlashtiradi.

    Admin router user routerdan OLDIN ro'yxatdan o'tkaziladi, chunki
    /admin buyrug'i va admin callbacklari alohida IsAdmin filtri bilan
    himoyalangan — tartib xavfsizlikka ta'sir qilmaydi, lekin aniqlik
    uchun admin avval tekshiriladi.
    """
    root = Router(name="root")
    root.include_router(admin_router)
    root.include_router(user_router)
    root.include_router(group_events.router)
    return root
