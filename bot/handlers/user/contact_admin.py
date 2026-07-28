# -*- coding: utf-8 -*-
"""bot/handlers/user/contact_admin.py — 'Admin bilan bog'lanish' bo'limi."""
from __future__ import annotations

from aiogram.types import Message

from bot.config import settings
from bot.keyboards.inline import contact_admin_keyboard
from bot.utils.text_templates import T


async def send_contact_admin(message: Message) -> None:
    await message.answer(
        T.CONTACT_ADMIN_TEXT.format(admin_name=settings.admin_name, admin_phone=settings.admin_phone),
        reply_markup=contact_admin_keyboard(),
    )
