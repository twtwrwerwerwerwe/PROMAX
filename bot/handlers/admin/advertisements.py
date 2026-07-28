# -*- coding: utf-8 -*-
"""bot/handlers/admin/advertisements.py — Admin panel: Faol/To'xtatilgan e'lonlar."""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError

from aiogram.types import CallbackQuery

from bot.core.containers import ServiceContainer
from bot.exceptions import AdvertisementNotFoundError
from bot.filters import IsAdmin
from bot.keyboards.admin_inline import admin_ads_list_keyboard, admin_back_keyboard
from bot.keyboards.callback_data import AdminAdActionCB, AdminAdListCB, AdminMenuCB
from bot.models.advertisement import AdStatus
from bot.scheduler.manager import SchedulerManager
from bot.utils.formatting import format_datetime, status_emoji, status_label_uz
from bot.utils.text_templates import T

logger = logging.getLogger("admin")

router = Router(name="admin_advertisements")
router.message.filter(F.chat.type == "private", IsAdmin())
router.callback_query.filter(F.message.chat.type == "private", IsAdmin())

PAGE_SIZE = 10
_STATUS_MAP = {"active_ads": AdStatus.ACTIVE.value, "stopped_ads": AdStatus.STOPPED.value}
_SHORT = {AdStatus.ACTIVE.value: "active", AdStatus.STOPPED.value: "stopped"}


@router.callback_query(AdminMenuCB.filter(F.section.in_(["active_ads", "stopped_ads"])))
async def on_ads_menu(callback: CallbackQuery, callback_data: AdminMenuCB, services: ServiceContainer) -> None:
    await callback.answer()
    status = _STATUS_MAP[callback_data.section]
    await _render_ads_list(callback, services, status, offset=0)


@router.callback_query(AdminAdListCB.filter())
async def on_ads_paginate(callback: CallbackQuery, callback_data: AdminAdListCB, services: ServiceContainer) -> None:
    await callback.answer()
    status = AdStatus.ACTIVE.value if callback_data.status == "active" else AdStatus.STOPPED.value
    await _render_ads_list(callback, services, status, offset=callback_data.offset)


async def _render_ads_list(callback: CallbackQuery, services: ServiceContainer, status: str, offset: int) -> None:
    ads = await services.advertisements.list_by_status(status, offset, PAGE_SIZE + 1)
    has_more = len(ads) > PAGE_SIZE
    ads = ads[:PAGE_SIZE]

    if not ads:
        await callback.message.answer(T.ADMIN_ADS_LIST_EMPTY, reply_markup=admin_back_keyboard())
        return

    lines = []
    for ad in ads:
        lines.append(
            f"{status_emoji(ad.status)} #{ad.id} | user={ad.user_id} | {status_label_uz(ad.status)} | "
            f"interval={ad.interval_minutes}min | yuborilgan={ad.total_sent_count} | {format_datetime(ad.updated_at)}"
        )
    text = "\n".join(lines)

    short_status = _SHORT.get(status, status)
    await callback.message.answer(text, reply_markup=admin_ads_list_keyboard(ads, short_status, offset, has_more))


@router.callback_query(AdminAdActionCB.filter(F.action == "force_stop"))
async def on_force_stop(callback: CallbackQuery, callback_data: AdminAdActionCB, services: ServiceContainer, scheduler: SchedulerManager, bot: Bot) -> None:
    await callback.answer()
    try:
        ad = await services.advertisements.stop(callback_data.ad_id, user_id=None)
    except AdvertisementNotFoundError:
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        return

    await scheduler.stop_job(ad.id)
    logger.info("Ad #%s admin=%s tomonidan majburiy to'xtatildi.", ad.id, callback.from_user.id)
    await callback.message.answer(T.AD_FORCE_STOPPED)
    try:
        await bot.send_message(ad.user_id, T.AD_FORCE_STOPPED_USER_NOTICE)
    except TelegramAPIError:
        pass
