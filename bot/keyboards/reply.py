# -*- coding: utf-8 -*-
"""bot/keyboards/reply.py — Reply klaviaturalar (faqat Asosiy menyu va telefon so'rash uchun)."""
from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.utils.text_templates import T


def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=T.BTN_SEND_AD)
    builder.button(text=T.BTN_EMERGENCY_STOP)
    builder.button(text=T.BTN_CONTACT_ADMIN)
    # Admin-only button
    if is_admin:
        builder.button(text=T.BTN_ADMIN_PANEL)
    builder.adjust(1, 1, 1, 1 if is_admin else None)
    return builder.as_markup(resize_keyboard=True)


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=T.ASK_PHONE_SHARE_BUTTON, request_contact=True))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
