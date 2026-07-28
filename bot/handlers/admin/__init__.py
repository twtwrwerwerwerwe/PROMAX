# -*- coding: utf-8 -*-
"""bot/handlers/admin/__init__.py — Admin handlerlarini bitta routerga yig'adi."""
from aiogram import Router

from bot.handlers.admin import advertisements, groups, panel, payments, users

admin_router = Router(name="admin_root")
admin_router.include_router(panel.router)
admin_router.include_router(payments.router)
admin_router.include_router(users.router)
admin_router.include_router(advertisements.router)
admin_router.include_router(groups.router)

__all__ = ["admin_router"]
