# -*- coding: utf-8 -*-
"""
main.py — Ilovaning kirish nuqtasi.
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.core.background_tasks import GroupValidatorLoop
from bot.core.logging_setup import setup_logging
from bot.database.engine import dispose_engine
from bot.handlers import build_root_router
from bot.middlewares import (
    BannedUserMiddleware,
    DatabaseMiddleware,
    ThrottlingMiddleware,
)
from bot.scheduler.manager import SchedulerManager
from bot.scheduler.recovery import recover_all_jobs
from bot.services.subscription_watcher import SubscriptionWatcher

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging()
    logger.info("Bot ishga tushirilmoqda...")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Use MemoryStorage: user requested no persistent FSM storage.
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # ---------------- Dependency Injection ----------------
    scheduler = SchedulerManager(bot)
    dp["scheduler"] = scheduler

    # ---------------- Middlewares ----------------
    db_middleware = DatabaseMiddleware(bot)
    throttling_middleware = ThrottlingMiddleware()
    banned_middleware = BannedUserMiddleware()

    for observer in (dp.message, dp.callback_query, dp.my_chat_member):
        observer.middleware(db_middleware)

    for observer in (dp.message, dp.callback_query):
        observer.middleware(throttling_middleware)
        observer.middleware(banned_middleware)

    # ---------------- Routers ----------------
    dp.include_router(build_root_router())

    # ---------------- Startup ----------------
    group_validator = GroupValidatorLoop(bot)
    subscription_watcher = SubscriptionWatcher(bot)

    async def on_startup():
        me = await bot.get_me()
        logger.info("Bot ishga tushdi: @%s (id=%s)", me.username, me.id)

        recovered = await recover_all_jobs(scheduler)
        logger.info(
            "Scheduler recovery yakunlandi: %s ta job tiklandi.",
            recovered,
        )

        group_validator.start()
        subscription_watcher.start()

    async def on_shutdown():
        logger.info("Bot to'xtatilmoqda...")

        await group_validator.stop()
        await subscription_watcher.stop()
        await scheduler.shutdown()
        await dispose_engine()

        await bot.session.close()

        logger.info("Bot muvaffaqiyatli to'xtatildi.")

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        logger.info("Polling yakunlandi.")


if __name__ == "__main__":
    try:
        import uvloop

        uvloop.install()
    except ImportError:
        pass

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot foydalanuvchi tomonidan to'xtatildi.")