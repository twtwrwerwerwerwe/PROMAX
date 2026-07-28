# -*- coding: utf-8 -*-
"""
bot/handlers/user/advertisement.py — E'lon yaratish, boshqarish va tahrirlash.

Ushbu modul spetsifikatsiyaning eng katta foydalanuvchi oqimini qamrab oladi:
matn -> interval -> tasdiqlash -> Boshlash -> Pauza/Davom/Tahrirlash/To'xtatish.
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.core.containers import ServiceContainer
from bot.exceptions import (
    AdvertisementAlreadyActiveError,
    AdvertisementNotFoundError,
    AdvertisementOwnershipError,
    SchedulerJobAlreadyRunningError,
)
from bot.keyboards.callback_data import AdPanelCB, ConfirmAdCB, EditChoiceCB, IntervalCB
from bot.keyboards.inline import ad_panel_keyboard, confirm_ad_keyboard, edit_choice_keyboard, interval_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.config import settings
from bot.models.advertisement import AdStatus, Advertisement
from bot.scheduler.manager import SchedulerManager
from bot.states.advertisement_states import AdCreationStates, AdEditStates
from bot.utils.formatting import format_datetime, status_emoji, status_label_uz
from bot.utils.text_templates import T

from bot.handlers.user.main_menu import ensure_ready

logger = logging.getLogger(__name__)

router = Router(name="user_advertisement")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")

MAX_AD_TEXT_LENGTH = 3500


def _panel_text(ad: Advertisement) -> str:
    return T.AD_STATUS_PANEL_TEMPLATE.format(
        status_emoji=status_emoji(ad.status),
        status_label=status_label_uz(ad.status),
        interval=ad.interval_minutes,
        sent_count=ad.total_sent_count,
        started_at=format_datetime(ad.started_at),
    )


async def _show_panel(target: Message, ad: Advertisement) -> None:
    await target.answer(_panel_text(ad), reply_markup=ad_panel_keyboard(ad.id, ad.status == AdStatus.PAUSED.value))


# ------------------------------------------------------------------
# Entry point: "📢 E'lon yuborish"
# ------------------------------------------------------------------
@router.message(F.text == T.BTN_SEND_AD)
async def on_send_ad_button(message: Message, services: ServiceContainer, state: FSMContext) -> None:
    user = await ensure_ready(message, services)
    if user is None:
        return

    existing = await services.advertisements.get_active_or_paused_for_user(user.telegram_id)
    if existing is not None:
        await _show_panel(message, existing)
        return

    await state.set_state(AdCreationStates.waiting_text)
    await message.answer(T.ASK_AD_TEXT)


@router.message(AdCreationStates.waiting_text, F.text)
async def on_ad_text_received(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    if not text.strip():
        await message.answer(T.AD_TEXT_EMPTY)
        return
    if len(text) > MAX_AD_TEXT_LENGTH:
        await message.answer(T.AD_TEXT_TOO_LONG.format(max_len=MAX_AD_TEXT_LENGTH))
        return

    await state.update_data(ad_text=text)
    await state.set_state(AdCreationStates.waiting_interval)
    await message.answer(T.ASK_INTERVAL, reply_markup=interval_keyboard(context="create"))


@router.message(AdCreationStates.waiting_text)
async def on_ad_text_invalid(message: Message) -> None:
    await message.answer(T.AD_TEXT_EMPTY)


@router.callback_query(IntervalCB.filter(F.context == "create"), AdCreationStates.waiting_interval)
async def on_interval_chosen_create(callback: CallbackQuery, callback_data: IntervalCB, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    ad_text = data.get("ad_text", "")

    await state.update_data(interval_minutes=callback_data.minutes)
    await state.set_state(AdCreationStates.waiting_confirmation)

    await callback.message.answer(
        T.CONFIRM_AD_TEMPLATE.format(ad_text=ad_text, interval=callback_data.minutes),
        reply_markup=confirm_ad_keyboard(),
    )


@router.callback_query(ConfirmAdCB.filter(F.action == "cancel"))
async def on_confirm_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(T.AD_CANCELLED, reply_markup=main_menu_keyboard(is_admin=(callback.from_user.id in settings.admin_ids)))


@router.callback_query(ConfirmAdCB.filter(F.action == "start"), AdCreationStates.waiting_confirmation)
async def on_confirm_start(
    callback: CallbackQuery, services: ServiceContainer, state: FSMContext, scheduler: SchedulerManager
) -> None:
    await callback.answer()
    data = await state.get_data()
    ad_text = data.get("ad_text")
    interval_minutes = data.get("interval_minutes")

    if not ad_text or not interval_minutes:
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        await state.clear()
        return

    try:
        ad = await services.advertisements.create_draft(callback.from_user.id, ad_text, interval_minutes)
    except AdvertisementAlreadyActiveError:
        await callback.message.answer(T.ALREADY_ACTIVE_AD, reply_markup=main_menu_keyboard(is_admin=(callback.from_user.id in settings.admin_ids)))
        await state.clear()
        return

    ad = await services.advertisements.activate(ad.id, callback.from_user.id)
    await state.clear()

    try:
        await scheduler.start_job(ad.id, start_running=True)
    except SchedulerJobAlreadyRunningError:
        logger.warning("Ad #%s uchun job allaqachon ishlamoqda edi (race).", ad.id)

    await callback.message.answer(T.AD_STARTED)
    await _show_panel(callback.message, ad)


# ------------------------------------------------------------------
# Ad control panel: Pause / Resume / Edit / Stop
# ------------------------------------------------------------------
@router.callback_query(AdPanelCB.filter(F.action == "pause"))
async def on_pause(callback: CallbackQuery, callback_data: AdPanelCB, services: ServiceContainer, scheduler: SchedulerManager) -> None:
    await callback.answer()
    try:
        ad = await services.advertisements.pause(callback_data.ad_id, callback.from_user.id)
    except (AdvertisementNotFoundError, AdvertisementOwnershipError):
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        return
    except ValueError:
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        return

    await scheduler.pause_job(ad.id)
    await callback.message.answer(T.AD_PAUSED)
    await _show_panel(callback.message, ad)


@router.callback_query(AdPanelCB.filter(F.action == "resume"))
async def on_resume(callback: CallbackQuery, callback_data: AdPanelCB, services: ServiceContainer, scheduler: SchedulerManager) -> None:
    await callback.answer()
    try:
        ad = await services.advertisements.resume(callback_data.ad_id, callback.from_user.id)
    except (AdvertisementNotFoundError, AdvertisementOwnershipError, ValueError):
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        return

    resumed = await scheduler.resume_job(ad.id)
    if not resumed:
        # Job registrda topilmadi (masalan restart oralig'ida) — xavfsiz tarzda qayta yaratamiz.
        try:
            await scheduler.start_job(ad.id, start_running=True)
        except SchedulerJobAlreadyRunningError:
            pass

    await callback.message.answer(T.AD_RESUMED)
    await _show_panel(callback.message, ad)


@router.callback_query(AdPanelCB.filter(F.action == "stop"))
async def on_stop(callback: CallbackQuery, callback_data: AdPanelCB, services: ServiceContainer, scheduler: SchedulerManager) -> None:
    await callback.answer()
    try:
        ad = await services.advertisements.stop(callback_data.ad_id, callback.from_user.id)
    except (AdvertisementNotFoundError, AdvertisementOwnershipError):
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        return

    await scheduler.stop_job(ad.id)
    await callback.message.answer(T.AD_STOPPED, reply_markup=main_menu_keyboard(is_admin=(callback.from_user.id in settings.admin_ids)))


@router.callback_query(AdPanelCB.filter(F.action == "edit"))
async def on_edit_open(callback: CallbackQuery, callback_data: AdPanelCB, services: ServiceContainer, state: FSMContext) -> None:
    await callback.answer()
    ad = await services.advertisements.get(callback_data.ad_id)
    if ad is None or ad.user_id != callback.from_user.id:
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        return

    await state.update_data(edit_ad_id=ad.id)
    await state.set_state(AdEditStates.choosing_field)
    await callback.message.answer(T.EDIT_CHOOSE_WHAT, reply_markup=edit_choice_keyboard(ad.id))


@router.callback_query(EditChoiceCB.filter(F.field == "back"))
async def on_edit_back(callback: CallbackQuery, callback_data: EditChoiceCB, services: ServiceContainer, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    ad = await services.advertisements.get(callback_data.ad_id)
    if ad is None or ad.user_id != callback.from_user.id:
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        return
    await _show_panel(callback.message, ad)


@router.callback_query(EditChoiceCB.filter(F.field == "text"))
async def on_edit_text_choice(callback: CallbackQuery, callback_data: EditChoiceCB, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(edit_ad_id=callback_data.ad_id)
    await state.set_state(AdEditStates.waiting_new_text)
    await callback.message.answer(T.ASK_NEW_AD_TEXT)


@router.callback_query(EditChoiceCB.filter(F.field == "interval"))
async def on_edit_interval_choice(callback: CallbackQuery, callback_data: EditChoiceCB, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(edit_ad_id=callback_data.ad_id)
    await state.set_state(AdEditStates.waiting_new_interval)
    await callback.message.answer(T.ASK_INTERVAL, reply_markup=interval_keyboard(context="edit"))


@router.callback_query(EditChoiceCB.filter(F.field == "both"))
async def on_edit_both_choice(callback: CallbackQuery, callback_data: EditChoiceCB, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(edit_ad_id=callback_data.ad_id)
    await state.set_state(AdEditStates.waiting_new_text_for_both)
    await callback.message.answer(T.ASK_NEW_AD_TEXT)


@router.message(AdEditStates.waiting_new_text, F.text)
async def on_new_text_received(message: Message, services: ServiceContainer, state: FSMContext) -> None:
    text = message.text or ""
    if not text.strip() or len(text) > MAX_AD_TEXT_LENGTH:
        await message.answer(T.AD_TEXT_EMPTY)
        return

    data = await state.get_data()
    ad_id = data.get("edit_ad_id")
    try:
        await services.advertisements.update_text(ad_id, message.from_user.id, text)
    except (AdvertisementNotFoundError, AdvertisementOwnershipError):
        await message.answer(T.UNKNOWN_CALLBACK)
        await state.clear()
        return

    await state.clear()
    await message.answer(T.AD_TEXT_UPDATED, reply_markup=main_menu_keyboard(is_admin=(message.from_user.id in settings.admin_ids)))


@router.callback_query(IntervalCB.filter(F.context == "edit"), AdEditStates.waiting_new_interval)
async def on_new_interval_received(callback: CallbackQuery, callback_data: IntervalCB, services: ServiceContainer, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    ad_id = data.get("edit_ad_id")
    try:
        await services.advertisements.update_interval(ad_id, callback.from_user.id, callback_data.minutes)
    except (AdvertisementNotFoundError, AdvertisementOwnershipError, ValueError):
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        await state.clear()
        return

    await state.clear()
    await callback.message.answer(T.AD_INTERVAL_UPDATED, reply_markup=main_menu_keyboard(is_admin=(callback.from_user.id in settings.admin_ids)))


@router.message(AdEditStates.waiting_new_text_for_both, F.text)
async def on_new_text_for_both(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    if not text.strip() or len(text) > MAX_AD_TEXT_LENGTH:
        await message.answer(T.AD_TEXT_EMPTY)
        return

    await state.update_data(new_text=text)
    await state.set_state(AdEditStates.waiting_new_interval_for_both)
    await message.answer(T.ASK_INTERVAL, reply_markup=interval_keyboard(context="edit_both"))


@router.callback_query(IntervalCB.filter(F.context == "edit_both"), AdEditStates.waiting_new_interval_for_both)
async def on_new_interval_for_both(callback: CallbackQuery, callback_data: IntervalCB, services: ServiceContainer, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    ad_id = data.get("edit_ad_id")
    new_text = data.get("new_text")

    try:
        await services.advertisements.update_text(ad_id, callback.from_user.id, new_text)
        await services.advertisements.update_interval(ad_id, callback.from_user.id, callback_data.minutes)
    except (AdvertisementNotFoundError, AdvertisementOwnershipError, ValueError):
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        await state.clear()
        return

    await state.clear()
    await callback.message.answer(T.AD_BOTH_UPDATED, reply_markup=main_menu_keyboard(is_admin=(callback.from_user.id in settings.admin_ids)))
