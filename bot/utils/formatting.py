# -*- coding: utf-8 -*-
"""bot/utils/formatting.py — Xabarlarni formatlash uchun yordamchi funksiyalar."""
from __future__ import annotations

import datetime as dt
from html import escape as html_escape

from bot.models.advertisement import AdStatus
from bot.models.user import User
from bot.utils.phone import format_phone_pretty, text_contains_phone
from bot.utils.text_templates import T


def escape_html(text: str) -> str:
    return html_escape(text, quote=False)


def compose_advertisement_text(raw_text: str, user: User) -> str:
    """Reklama matniga foydalanuvchi telefon raqamini qo'shish kerak bo'lsa qo'shadi.

    Agar foydalanuvchi matn ichida o'zi telefon raqami yozgan bo'lsa —
    o'zgartirmasdan qoldiradi. Aks holda profildagi saqlangan raqamni
    oxiriga qo'shadi.
    """
    if text_contains_phone(raw_text):
        return raw_text
    if user.phone_number:
        pretty = format_phone_pretty(user.phone_number)
        return f"{raw_text}\n\n📞 {pretty}"
    return raw_text


def render_group_message(ad_text_with_phone: str) -> str:
    """Guruhga yuboriladigan yakuniy HTML formatidagi xabarni tayyorlaydi.

    `ad_text_with_phone` allaqachon `compose_advertisement_text` orqali
    telefon raqami bilan (agar kerak bo'lsa) tayyorlangan bo'lishi kerak —
    shuning uchun bu yerda qayta telefon qo'shilmaydi (dublikatning oldi olinadi).
    """
    return T.GROUP_AD_TEMPLATE.format(ad_text=ad_text_with_phone)


def format_datetime(value: dt.datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M")


def status_emoji(status: str) -> str:
    return {
        AdStatus.CREATED.value: "🟡",
        AdStatus.ACTIVE.value: "🟢",
        AdStatus.PAUSED.value: "⏸",
        AdStatus.STOPPED.value: "🔴",
    }.get(status, "⚪️")


def status_label_uz(status: str) -> str:
    return {
        AdStatus.CREATED.value: "Yaratilgan",
        AdStatus.ACTIVE.value: "Aktiv",
        AdStatus.PAUSED.value: "Pauza",
        AdStatus.STOPPED.value: "To'xtatilgan",
    }.get(status, status)


def build_driver_contact_url(telegram_id: int, username: str | None) -> str:
    """Haydovchi bilan bog'lanish uchun URL — username bo'lsa t.me/username,
    bo'lmasa tg://user?id=... ishlatiladi."""
    if username:
        return f"https://t.me/{username}"
    return f"tg://user?id={telegram_id}"
