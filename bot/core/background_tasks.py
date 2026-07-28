# -*- coding: utf-8 -*-
"""
bot/core/background_tasks.py — Guruhlarni davriy tekshiruvchi fon jarayon.

Har necha soatda (GROUP_VALIDATION_INTERVAL_HOURS) barcha faol guruhlarni
qayta tekshiradi: bot hali ham admin ekanligini tasdiqlaydi, aks holda
guruhni nofaol qiladi (o'chirmasdan).
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from bot.config import settings
from bot.database.engine import get_session
from bot.repositories import GroupRepository
from bot.services.group_service import GroupService

logger = logging.getLogger(__name__)


class GroupValidatorLoop:
    def __init__(self, bot: Bot):
        self.bot = bot
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self) -> None:
        if self._task is not None:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="group-validator")
        logger.info("Group validator loop ishga tushdi (har %s soatda).", settings.group_validation_interval_hours)

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        # Bot ishga tushganida darhol bir marta tekshiradi, keyin davriy davom etadi.
        while self._running:
            try:
                async with get_session() as session:
                    service = GroupService(GroupRepository(session), self.bot)
                    await service.revalidate_all()
            except Exception as exc:  # noqa: BLE001 — fon jarayon hech qachon o'lmasligi kerak
                # Log a concise warning to avoid noisy stack traces when DB is temporarily unreachable.
                logger.warning("Group validator iteration failed: %s", exc)
            await asyncio.sleep(settings.group_validation_interval_hours * 3600)
