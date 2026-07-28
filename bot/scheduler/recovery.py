# -*- coding: utf-8 -*-
"""
bot/scheduler/recovery.py — Server qayta ishga tushganda e'lonlarni tiklash.

Foydalanuvchilar hech qachon qo'lda qayta ishga tushirishi shart emas —
bot ishga tushganda bazadagi ACTIVE va PAUSED e'lonlar uchun avtomatik
ravishda scheduler job'lari qayta yaratiladi.
"""
from __future__ import annotations

import logging

from sqlalchemy import select

from bot.database.engine import get_session
from bot.models.advertisement import AdStatus, Advertisement
from bot.scheduler.manager import SchedulerManager

logger = logging.getLogger("scheduler")


async def recover_all_jobs(scheduler: SchedulerManager) -> int:
    """Bazadan ACTIVE va PAUSED e'lonlarni o'qib, ularga mos job'larni qayta ishga tushiradi.

    Returns tiklangan job'lar soni.
    """
    recovered = 0
    async with get_session() as session:
        result = await session.execute(
            select(Advertisement).where(
                Advertisement.status.in_([AdStatus.ACTIVE.value, AdStatus.PAUSED.value])
            )
        )
        ads = result.scalars().all()

    for ad in ads:
        try:
            await scheduler.start_job(ad.id, start_running=(ad.status == AdStatus.ACTIVE.value))
            recovered += 1
        except Exception:  # noqa: BLE001
            logger.exception("Ad #%s tiklashda xatolik.", ad.id)

    logger.info("Scheduler recovery: %s ta e'lon tiklandi.", recovered)
    return recovered
