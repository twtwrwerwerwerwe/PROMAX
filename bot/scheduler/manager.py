# -*- coding: utf-8 -*-
"""
bot/scheduler/manager.py — Barcha ishlayotgan job'lar registri.

Bitta e'lon uchun faqat bitta Task borligini kafolatlaydi (duplicate
job himoyasi), pauza/davom ettirish/to'xtatishni markazlashtiradi,
va bot qayta ishga tushganda ACTIVE/PAUSED e'lonlarni avtomatik tiklaydi.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, List

from aiogram import Bot

from bot.config import settings
from bot.exceptions import SchedulerJobAlreadyRunningError
from bot.scheduler.engine import AdvertisementWorker, JobControl

logger = logging.getLogger("scheduler")


class SchedulerManager:
    """Reklama yuborish job'larining markaziy boshqaruvchisi (Singleton sifatida ishlatiladi)."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self._jobs: Dict[int, JobControl] = {}
        self._send_semaphore = asyncio.Semaphore(settings.send_concurrency_limit)
        self._lock = asyncio.Lock()

    def is_running(self, ad_id: int) -> bool:
        job = self._jobs.get(ad_id)
        return job is not None and job.task is not None and not job.task.done()

    async def start_job(self, ad_id: int, *, start_running: bool = True) -> None:
        """Yangi job yaratadi. Agar shu ad_id uchun allaqachon job ishlayotgan bo'lsa xato ko'taradi."""
        async with self._lock:
            if self.is_running(ad_id):
                raise SchedulerJobAlreadyRunningError(f"Ad #{ad_id} uchun job allaqachon ishlamoqda")

            control = JobControl(ad_id=ad_id)
            if start_running:
                control.running.set()
            worker = AdvertisementWorker(self.bot, control, self._send_semaphore)
            task = asyncio.create_task(worker.run(), name=f"ad-worker-{ad_id}")
            control.task = task
            self._jobs[ad_id] = control

            task.add_done_callback(lambda t, aid=ad_id: self._on_job_done(aid, t))
            logger.info("Scheduler job boshlandi: ad_id=%s (running=%s)", ad_id, start_running)

    def _on_job_done(self, ad_id: int, task: asyncio.Task) -> None:
        # Finished/cancelled tasklarni registridan tozalash — memory leak'ning oldini oladi.
        current = self._jobs.get(ad_id)
        if current is not None and current.task is task:
            self._jobs.pop(ad_id, None)
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.error("Ad #%s worker kutilmagan xatolik bilan tugadi: %s", ad_id, exc)

    async def pause_job(self, ad_id: int) -> bool:
        job = self._jobs.get(ad_id)
        if job is None:
            return False
        job.running.clear()
        logger.info("Scheduler job pauza qilindi: ad_id=%s", ad_id)
        return True

    async def resume_job(self, ad_id: int) -> bool:
        job = self._jobs.get(ad_id)
        if job is None:
            return False
        job.running.set()
        logger.info("Scheduler job davom ettirildi: ad_id=%s", ad_id)
        return True

    async def stop_job(self, ad_id: int) -> bool:
        """Job'ni butunlay to'xtatadi va barcha resurslarni tozalaydi."""
        job = self._jobs.pop(ad_id, None)
        if job is None or job.task is None:
            return False
        job.running.set()  # agar pauza kutayotgan bo'lsa, uyg'otish uchun
        job.task.cancel()
        try:
            await job.task
        except asyncio.CancelledError:
            pass
        except Exception:  # noqa: BLE001
            logger.exception("Ad #%s job to'xtatishda kutilmagan xatolik.", ad_id)
        logger.info("Scheduler job to'xtatildi: ad_id=%s", ad_id)
        return True

    async def emergency_stop(self, ad_id: int) -> None:
        """Ikkilamchi xavfsizlik: job mavjud bo'lmasa ham xatosiz ishlaydi."""
        await self.stop_job(ad_id)

    async def shutdown(self) -> None:
        """Bot to'xtaganda barcha job'larni xavfsiz to'xtatadi (orphan task qoldirmaslik uchun)."""
        ad_ids: List[int] = list(self._jobs.keys())
        for ad_id in ad_ids:
            await self.stop_job(ad_id)
        logger.info("Barcha scheduler job'lari to'xtatildi (shutdown).")

    def running_count(self) -> int:
        return len(self._jobs)
