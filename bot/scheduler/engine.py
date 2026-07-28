# -*- coding: utf-8 -*-
"""
bot/scheduler/engine.py — Reklama yuborish dvigateli (eng muhim modul).

Har bir aktiv e'lon uchun bitta asyncio Task ishlaydi ("bir foydalanuvchi —
bitta job" qoidasi). Job o'zining `JobControl.running` Event'i orqali
pauza/davom ettirish holatini boshqaradi, `asyncio.Task.cancel()` orqali
butunlay to'xtatiladi.

Har bir iteratsiyada:
    1. Bazadan (source of truth) e'lonning joriy holati/matni/intervali
       qayta o'qiladi.
    2. Agar STOPPED bo'lsa yoki 24 soat muddati tugagan bo'lsa — chiqiladi.
    3. Pauza bo'lsa — navbatdagi yuborishgacha kutiladi (cancellable wait).
    4. Barcha faol guruhlarga bog'langan concurrency (Semaphore) bilan,
       har bir guruh mustaqil xato-chidamli tarzda xabar yuboradi.
    5. Interval bo'yicha uxlaydi (cancellable sleep) va davom etadi.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
from dataclasses import dataclass, field
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import settings
from bot.database.engine import get_session
from bot.models.advertisement import AdStatus
from bot.repositories import AdvertisementRepository, GroupRepository, UserRepository
from bot.utils.formatting import build_driver_contact_url, compose_advertisement_text, render_group_message
from bot.utils.text_templates import T

logger = logging.getLogger("scheduler")


@dataclass
class JobControl:
    """Bitta e'lon (job) uchun ish vaqtidagi boshqaruv holati."""
    ad_id: int
    running: asyncio.Event = field(default_factory=asyncio.Event)
    task: Optional[asyncio.Task] = None


class AdvertisementWorker:
    """Bitta e'lon uchun yuborish tsiklini bajaradigan sinf."""

    def __init__(self, bot: Bot, control: JobControl, send_semaphore: asyncio.Semaphore):
        self.bot = bot
        self.control = control
        self.send_semaphore = send_semaphore

    async def run(self) -> None:
        ad_id = self.control.ad_id
        try:
            while True:
                snapshot = await self._load_snapshot(ad_id)
                if snapshot is None:
                    logger.info("Ad #%s topilmadi, worker to'xtaydi.", ad_id)
                    return
                status, interval_minutes, text, user_id, username, phone, expires_at = snapshot

                if status == AdStatus.STOPPED.value:
                    logger.info("Ad #%s STOPPED, worker chiqmoqda.", ad_id)
                    return

                if expires_at is not None and dt.datetime.now(dt.timezone.utc) >= expires_at:
                    await self._auto_stop(ad_id, user_id)
                    return

                # Pauza bo'lsa shu yerda kutadi (cancel orqali darhol uzilishi mumkin).
                await self.control.running.wait()

                await self._broadcast(ad_id, text, user_id, username, phone)

                await asyncio.sleep(interval_minutes * 60)
        except asyncio.CancelledError:
            logger.info("Ad #%s worker bekor qilindi (cancel).", ad_id)
            raise

    # ------------------------------------------------------------------
    async def _load_snapshot(self, ad_id: int):
        async with get_session() as session:
            ad_repo = AdvertisementRepository(session)
            user_repo = UserRepository(session)
            ad = await ad_repo.get(ad_id)
            if ad is None:
                return None
            user = await user_repo.get(ad.user_id)
            return (
                ad.status,
                ad.interval_minutes,
                ad.text,
                ad.user_id,
                user.username if user else None,
                user.phone_number if user else None,
                ad.expires_at,
            )

    async def _auto_stop(self, ad_id: int, user_id: int) -> None:
        async with get_session() as session:
            ad_repo = AdvertisementRepository(session)
            await ad_repo.set_status(ad_id, AdStatus.STOPPED.value)
        logger.info("Ad #%s 24 soatdan so'ng avtomatik to'xtatildi.", ad_id)
        try:
            await self.bot.send_message(user_id, T.AD_AUTO_STOPPED)
        except Exception:  # noqa: BLE001
            logger.warning("Foydalanuvchi %s ga auto-stop xabari yuborilmadi.", user_id)

    async def _broadcast(self, ad_id: int, text: str, user_id: int, username: Optional[str], phone: Optional[str]) -> None:
        async with get_session() as session:
            group_repo = GroupRepository(session)
            groups = list(await group_repo.list_active())

        if not groups:
            logger.info("Ad #%s uchun faol guruh mavjud emas, yuborish o'tkazib yuborildi.", ad_id)
            return

        class _U:
            telegram_id = user_id
            phone_number = phone

        composed = compose_advertisement_text(text, _U())  # type: ignore[arg-type]
        html_message = render_group_message(composed)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text=T.BTN_CONTACT_DRIVER,
                    url=build_driver_contact_url(user_id, username),
                )
            ]]
        )

        results = await asyncio.gather(
            *[self._send_one(group.chat_id, html_message, keyboard) for group in groups]
        )
        success_count = sum(1 for ok in results if ok)
        if success_count:
            async with get_session() as session:
                ad_repo = AdvertisementRepository(session)
                ad = await ad_repo.get(ad_id)
                if ad is not None:
                    ad.total_sent_count += success_count
                    ad.last_sent_at = dt.datetime.now(dt.timezone.utc)
                    await session.flush()
        logger.info("Ad #%s: %s/%s guruhga muvaffaqiyatli yuborildi.", ad_id, success_count, len(groups))

    async def _send_one(self, chat_id: int, html_message: str, keyboard: InlineKeyboardMarkup) -> bool:
        async with self.send_semaphore:
            attempts = 0
            while attempts <= settings.flood_wait_max_retries:
                attempts += 1
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=html_message,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                        disable_web_page_preview=True,
                    )
                    return True
                except TelegramRetryAfter as exc:
                    logger.warning("FloodWait guruh=%s: %s soniya kutilmoqda.", chat_id, exc.retry_after)
                    await asyncio.sleep(exc.retry_after)
                    continue
                except TelegramForbiddenError:
                    logger.warning("Guruh %s botni chiqarib yuborgan, nofaol qilinmoqda.", chat_id)
                    await self._deactivate_group(chat_id, "forbidden")
                    return False
                except TelegramBadRequest as exc:
                    logger.error("Guruh %s ga yuborishda BadRequest: %s", chat_id, exc)
                    return False
                except (TelegramNetworkError, TelegramServerError) as exc:
                    logger.warning("Tarmoq/server xatoligi guruh=%s (urinish %s): %s", chat_id, attempts, exc)
                    await asyncio.sleep(min(2 ** attempts, 30))
                    continue
                except Exception:  # noqa: BLE001 — bitta guruhdagi xato boshqalarga ta'sir qilmasin
                    logger.exception("Guruh %s ga yuborishda kutilmagan xatolik.", chat_id)
                    return False
            logger.error("Guruh %s: max urinishlar tugadi, xabar yuborilmadi.", chat_id)
            return False

    async def _deactivate_group(self, chat_id: int, reason: str) -> None:
        async with get_session() as session:
            group_repo = GroupRepository(session)
            await group_repo.set_active(chat_id, False, error=reason)
