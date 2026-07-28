# -*- coding: utf-8 -*-
"""bot/handlers/user/start.py — /start buyrug'i (faqat shaxsiy chatda)."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.core.containers import ServiceContainer
from bot.keyboards.inline import continue_keyboard
from bot.utils.text_templates import T
import datetime as dt

logger = logging.getLogger(__name__)

router = Router(name="user_start")
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
async def cmd_start(message: Message, services: ServiceContainer) -> None:
    user = message.from_user
    created_user = await services.users.get_or_create(user.id, user.username, user.full_name)

    groups_count = await services.groups.count_active()

    # Show start greeting only for newly created users (within last 60 seconds).
    created_at = getattr(created_user, "created_at", None)
    show_greeting = False
    if created_at is None:
        show_greeting = True
    else:
        now = dt.datetime.now(dt.timezone.utc)
        try:
            delta = abs((now - created_at).total_seconds())
            if delta < 60:
                show_greeting = True
        except Exception:
            show_greeting = True

    if show_greeting:
        await message.answer(
            T.START_GREETING.format(groups_count=groups_count),
            reply_markup=continue_keyboard(),
        )
