# -*- coding: utf-8 -*-
"""bot/handlers/admin/panel.py — Admin panelning bosh menyusi, statistikalar, sozlamalar."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.core.containers import ServiceContainer
from bot.filters import IsAdmin
from bot.keyboards.admin_inline import admin_back_keyboard, admin_root_keyboard
from bot.keyboards.callback_data import AdminMenuCB
from bot.utils.text_templates import T

logger = logging.getLogger("admin")

router = Router(name="admin_panel")
router.message.filter(F.chat.type == "private", IsAdmin())
router.callback_query.filter(F.message.chat.type == "private", IsAdmin())


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    logger.info("Admin panel ochildi: admin_id=%s", message.from_user.id)
    await message.answer(T.ADMIN_PANEL_TITLE, reply_markup=admin_root_keyboard())


@router.callback_query(AdminMenuCB.filter(F.section == "root"))
async def on_admin_root(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(T.ADMIN_PANEL_TITLE, reply_markup=admin_root_keyboard())


@router.callback_query(AdminMenuCB.filter(F.section == "stats"))
async def on_admin_stats(callback: CallbackQuery, services: ServiceContainer) -> None:
    await callback.answer()
    stats = await services.admin.get_statistics()
    await callback.message.answer(
        T.ADMIN_STATS_TEMPLATE.format(
            total_users=stats.total_users,
            active_subs=stats.active_subs,
            active_ads=stats.active_ads,
            stopped_ads=stats.stopped_ads,
            active_groups=stats.active_groups,
            pending_payments=stats.pending_payments,
            approved_payments=stats.approved_payments,
        ),
        reply_markup=admin_back_keyboard(),
    )


@router.callback_query(AdminMenuCB.filter(F.section == "settings"))
async def on_admin_settings(callback: CallbackQuery, services: ServiceContainer) -> None:
    await callback.answer()
    values = await services.admin.get_effective_settings()
    await callback.message.answer(
        T.ADMIN_SETTINGS_TITLE + "\n\n" + T.ADMIN_SETTINGS_BODY.format(**values),
        reply_markup=admin_back_keyboard(),
    )
