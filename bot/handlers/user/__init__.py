# -*- coding: utf-8 -*-
"""bot/handlers/user/__init__.py — Foydalanuvchi handlerlarini bitta routerga yig'adi."""
from aiogram import Router

from bot.handlers.user import advertisement, main_menu, payment, phone, start

user_router = Router(name="user_root")
user_router.include_router(start.router)
user_router.include_router(payment.router)
user_router.include_router(phone.router)
user_router.include_router(main_menu.router)
user_router.include_router(advertisement.router)

__all__ = ["user_router"]
