# -*- coding: utf-8 -*-
"""bot/handlers/admin/users.py — Admin panel: Foydalanuvchilar bo'limi."""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery

from bot.core.containers import ServiceContainer
from bot.filters import IsAdmin
from bot.keyboards.admin_inline import admin_back_keyboard, admin_users_list_keyboard
from bot.keyboards.callback_data import AdminMenuCB, AdminUserActionCB, AdminUserListCB
from bot.utils.formatting import format_datetime
from bot.utils.phone import format_phone_pretty
from bot.utils.text_templates import T

logger = logging.getLogger("admin")

router = Router(name="admin_users")
router.message.filter(F.chat.type == "private", IsAdmin())
router.callback_query.filter(F.message.chat.type == "private", IsAdmin())

PAGE_SIZE = 10


@router.callback_query(AdminMenuCB.filter(F.section == "users"))
async def on_users_menu(callback: CallbackQuery, services: ServiceContainer) -> None:
    await callback.answer()
    await _render_users_list(callback, services, offset=0)


@router.callback_query(AdminUserListCB.filter())
async def on_users_paginate(callback: CallbackQuery, callback_data: AdminUserListCB, services: ServiceContainer) -> None:
    await callback.answer()
    await _render_users_list(callback, services, offset=callback_data.offset)


async def _render_users_list(callback: CallbackQuery, services: ServiceContainer, offset: int) -> None:
    users = await services.users.list_paginated(offset, PAGE_SIZE + 1)
    has_more = len(users) > PAGE_SIZE
    users = users[:PAGE_SIZE]

    if not users:
        await callback.message.answer(T.ADMIN_USERS_LIST_EMPTY, reply_markup=admin_back_keyboard())
        return

    lines = []
    for user in users:
        phone = format_phone_pretty(user.phone_number) if user.phone_number else "—"
        lines.append(
            T.ADMIN_USER_CARD.format(
                display_name=user.display_name,
                telegram_id=user.telegram_id,
                phone=phone,
                sub_status=user.subscription_status,
                created_at=format_datetime(user.created_at),
            )
        )
    text = "\n━━━━━━━━━━━━━━\n".join(lines)

    await callback.message.answer(text, reply_markup=admin_users_list_keyboard(users, offset, has_more))


@router.callback_query(AdminUserActionCB.filter(F.action == "ban"))
async def on_ban_user(callback: CallbackQuery, callback_data: AdminUserActionCB, services: ServiceContainer, bot: Bot) -> None:
    await callback.answer()
    await services.users.set_banned(callback_data.user_id, True)
    logger.info("Foydalanuvchi %s bloklandi (admin=%s)", callback_data.user_id, callback.from_user.id)
    await callback.message.answer(T.USER_BANNED)
    try:
        await bot.send_message(callback_data.user_id, T.USER_IS_BANNED_MSG)
    except TelegramAPIError:
        pass


@router.callback_query(AdminUserActionCB.filter(F.action == "unban"))
async def on_unban_user(callback: CallbackQuery, callback_data: AdminUserActionCB, services: ServiceContainer) -> None:
    await callback.answer()
    await services.users.set_banned(callback_data.user_id, False)
    logger.info("Foydalanuvchi %s blokdan chiqarildi (admin=%s)", callback_data.user_id, callback.from_user.id)
    await callback.message.answer(T.USER_UNBANNED)
