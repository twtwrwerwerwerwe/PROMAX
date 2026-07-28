# -*- coding: utf-8 -*-
"""bot/keyboards/inline.py — Foydalanuvchi uchun inline klaviaturalar."""
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import Tariff, settings
from bot.keyboards.callback_data import (
    AdPanelCB,
    ConfirmAdCB,
    ContinueCB,
    EditChoiceCB,
    IntervalCB,
    PayMethodCB,
    TariffCB,
)
from bot.utils.formatting import build_driver_contact_url
from bot.utils.text_templates import T


def continue_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=T.CONTINUE_BUTTON, callback_data=ContinueCB())
    return builder.as_markup()


def tariffs_keyboard(tariffs: dict[str, Tariff]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, tariff in tariffs.items():
        label = T.TARIFF_BUTTON_FMT.format(label=tariff.label, price=f"{tariff.price:,}".replace(",", " "))
        builder.button(text=label, callback_data=TariffCB(tariff_key=key))
    builder.adjust(1)
    return builder.as_markup()


def payment_methods_keyboard(tariff_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=T.PAY_METHOD_RECEIPT, callback_data=PayMethodCB(tariff_key=tariff_key, method="receipt"))
    builder.button(text=T.PAY_METHOD_CLICK, callback_data=PayMethodCB(tariff_key=tariff_key, method="click"))
    builder.button(text=T.PAY_METHOD_PAYME, callback_data=PayMethodCB(tariff_key=tariff_key, method="payme"))
    builder.button(
        text=T.PAY_METHOD_CONTACT_ADMIN,
        callback_data=PayMethodCB(tariff_key=tariff_key, method="contact_admin"),
    )
    builder.adjust(1)
    return builder.as_markup()


def interval_keyboard(context: str = "create") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for minutes in settings.ad_intervals:
        builder.button(text=T.INTERVAL_BUTTON_FMT.format(minutes=minutes), callback_data=IntervalCB(minutes=minutes, context=context))
    builder.adjust(2)
    return builder.as_markup()


def confirm_ad_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=T.BTN_START_AD, callback_data=ConfirmAdCB(action="start"))
    builder.button(text=T.BTN_CANCEL, callback_data=ConfirmAdCB(action="cancel"))
    builder.adjust(1)
    return builder.as_markup()


def ad_panel_keyboard(ad_id: int, is_paused: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_paused:
        builder.button(text=T.BTN_RESUME, callback_data=AdPanelCB(ad_id=ad_id, action="resume"))
    else:
        builder.button(text=T.BTN_PAUSE, callback_data=AdPanelCB(ad_id=ad_id, action="pause"))
    builder.button(text=T.BTN_EDIT, callback_data=AdPanelCB(ad_id=ad_id, action="edit"))
    builder.button(text=T.BTN_STOP, callback_data=AdPanelCB(ad_id=ad_id, action="stop"))
    builder.adjust(1)
    return builder.as_markup()


def edit_choice_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=T.BTN_EDIT_TEXT, callback_data=EditChoiceCB(ad_id=ad_id, field="text"))
    builder.button(text=T.BTN_EDIT_INTERVAL, callback_data=EditChoiceCB(ad_id=ad_id, field="interval"))
    builder.button(text=T.BTN_EDIT_BOTH, callback_data=EditChoiceCB(ad_id=ad_id, field="both"))
    builder.button(text=T.BTN_BACK, callback_data=EditChoiceCB(ad_id=ad_id, field="back"))
    builder.adjust(1)
    return builder.as_markup()


def contact_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=T.BTN_PROFILE, url=settings.admin_profile_url)
    return builder.as_markup()


def driver_contact_keyboard(telegram_id: int, username: str | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=T.BTN_CONTACT_DRIVER, url=build_driver_contact_url(telegram_id, username))
    return builder.as_markup()
