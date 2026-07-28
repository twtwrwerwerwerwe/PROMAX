# -*- coding: utf-8 -*-
"""bot/handlers/user/main_menu.py — Asosiy menyu (3 tugma)."""
from __future__ import annotations

import logging
from typing import Optional

from aiogram import F, Router
from aiogram.types import Message

from bot.core.containers import ServiceContainer
from bot.keyboards.reply import main_menu_keyboard, phone_request_keyboard
from bot.config import settings
from bot.keyboards.admin_inline import admin_root_keyboard
from bot.models.user import User
from bot.scheduler.manager import SchedulerManager
from bot.utils.text_templates import T

logger = logging.getLogger(__name__)

router = Router(name="user_main_menu")
router.message.filter(F.chat.type == "private")


async def show_main_menu(message: Message, services: ServiceContainer) -> None:
    await message.answer(T.MAIN_MENU_TEXT, reply_markup=main_menu_keyboard(is_admin=(message.from_user.id in settings.admin_ids)))


@router.message(F.text == T.BTN_ADMIN_PANEL)
async def on_admin_panel_button(message: Message) -> None:
    if message.from_user.id not in settings.admin_ids:
        await message.answer(T.ADMIN_ACCESS_DENIED)
        return

    await message.answer(T.ADMIN_PANEL_TITLE, reply_markup=admin_root_keyboard())


async def ensure_ready(message: Message, services: ServiceContainer) -> Optional[User]:
    """Foydalanuvchi obunasi va telefon raqami borligini tekshiradi.

    Agar tayyor bo'lmasa — mos xabar yuboradi va None qaytaradi.
    """
    user = await services.users.get_or_create(message.from_user.id, message.from_user.username, message.from_user.full_name)

    if not user.has_active_subscription:
        await message.answer(T.SUBSCRIPTION_REQUIRED)
        return None

    if not user.phone_number:
        await message.answer(T.PHONE_NOT_REGISTERED, reply_markup=phone_request_keyboard())
        return None

    return user


@router.message(F.text == T.BTN_CONTACT_ADMIN)
async def on_contact_admin_button(message: Message, services: ServiceContainer) -> None:
    from bot.handlers.user.contact_admin import send_contact_admin
    await send_contact_admin(message)


@router.message(F.text == T.BTN_EMERGENCY_STOP)
async def on_emergency_stop(message: Message, services: ServiceContainer, scheduler: SchedulerManager) -> None:
    user = await ensure_ready(message, services)
    if user is None:
        return

    ad = await services.advertisements.get_active_or_paused_for_user(user.telegram_id)
    if ad is None:
        await message.answer(T.NO_ACTIVE_AD_TO_STOP, reply_markup=main_menu_keyboard(is_admin=(message.from_user.id in settings.admin_ids)))
        return

    await scheduler.emergency_stop(ad.id)
    await services.advertisements.stop(ad.id, user.telegram_id)
    logger.info("Emergency stop: user=%s ad=%s", user.telegram_id, ad.id)

    await message.answer(T.EMERGENCY_STOP_DONE, reply_markup=main_menu_keyboard(is_admin=(message.from_user.id in settings.admin_ids)))
