# -*- coding: utf-8 -*-
"""
bot/services/subscription_watcher.py — Obuna muddatini kuzatuvchi fon jarayoni.

Eski loyihadagi `background.py` ichidagi `subscription_watch_loop` mantig'ining
porti: muddati tugagan obunalarni EXPIRED qiladi, 3 kun va 1 kun qolganda
foydalanuvchiga bir marta (flag orqali) eslatma yuboradi.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot.config import settings
from bot.database.engine import get_session
from bot.models.advertisement import AdStatus
from bot.repositories import AdvertisementRepository, UserRepository
from bot.utils.text_templates import T

logger = logging.getLogger("payment")


class SubscriptionWatcher:
    """Davriy ravishda barcha foydalanuvchilar obunasini tekshiradi."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self) -> None:
        if self._task is not None:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="subscription-watcher")
        logger.info("Subscription watcher ishga tushdi.")

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Subscription watcher to'xtatildi.")

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._check_once()
            except Exception:  # noqa: BLE001 — fon jarayon hech qachon o'lmasligi kerak
                logger.exception("Subscription watcher iteratsiyasida xatolik")
            await asyncio.sleep(settings.background_loop_interval_seconds)

    async def _check_once(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        reminder_threshold = dt.timedelta(days=settings.subscription_reminder_days_before)

        async with get_session() as session:
            user_repo = UserRepository(session)
            ad_repo = AdvertisementRepository(session)
            users = await user_repo.list_expiring_subscriptions()

            for user in users:
                end = user.subscription_end
                if end is None:
                    continue
                if end.tzinfo is None:
                    end = end.replace(tzinfo=dt.timezone.utc)

                remaining = end - now

                if remaining <= dt.timedelta(0):
                    await user_repo.expire_subscription(user.telegram_id)
                    active_ad = await ad_repo.get_active_for_user(user.telegram_id)
                    if active_ad is not None:
                        await ad_repo.set_status(active_ad.id, AdStatus.STOPPED.value)
                    await self._safe_send(user.telegram_id, T.SUBSCRIPTION_EXPIRED)
                    continue

                if remaining <= dt.timedelta(days=1) and not user.reminder_1day_sent:
                    await self._safe_send(user.telegram_id, T.SUBSCRIPTION_REMINDER_1DAY)
                    await user_repo.mark_reminder_sent(user.telegram_id, one_day=True)
                elif remaining <= reminder_threshold and not user.reminder_3day_sent:
                    await self._safe_send(user.telegram_id, T.SUBSCRIPTION_REMINDER_3DAY)
                    await user_repo.mark_reminder_sent(user.telegram_id, three_day=True)

    async def _safe_send(self, telegram_id: int, text: str) -> None:
        try:
            await self.bot.send_message(telegram_id, text)
        except TelegramAPIError as exc:
            logger.warning("Foydalanuvchi %s ga eslatma yuborilmadi: %s", telegram_id, exc)
