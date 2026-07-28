# -*- coding: utf-8 -*-
"""
bot/core/logging_setup.py — Professional logging konfiguratsiyasi.

Har bir kichik tizim uchun alohida rotatsiyalanuvchi log fayl:
    logs/bot.log        — umumiy bot hodisalari
    logs/scheduler.log  — reklama yuborish dvigateli
    logs/payment.log    — to'lov tizimi
    logs/admin.log      — admin panel harakatlari
    logs/errors.log     — barcha ERROR va undan yuqori darajadagi xatoliklar

Disk hajmi cheksiz o'smasligi uchun RotatingFileHandler ishlatiladi.
"""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from bot.config import settings

_MAX_BYTES = 10 * 1024 * 1024  # 10 MB per file
_BACKUP_COUNT = 5

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _build_file_handler(filename: str, level: int = logging.INFO) -> RotatingFileHandler:
    path = os.path.join(settings.log_dir, filename)
    handler = RotatingFileHandler(path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8")
    handler.setFormatter(_FORMATTER)
    handler.setLevel(level)
    return handler


def setup_logging() -> None:
    """Initializes all loggers. Must be called once, at application startup."""
    os.makedirs(settings.log_dir, exist_ok=True)

    root_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(root_level)

    console = logging.StreamHandler()
    console.setFormatter(_FORMATTER)
    console.setLevel(root_level)
    root.addHandler(console)
    root.addHandler(_build_file_handler("bot.log", root_level))
    root.addHandler(_build_file_handler("errors.log", logging.ERROR))

    # Dedicated subsystem loggers propagate to root too (so errors.log still
    # captures everything) but additionally write to their own file.
    for logger_name, filename in (
        ("scheduler", "scheduler.log"),
        ("payment", "payment.log"),
        ("admin", "admin.log"),
    ):
        logger = logging.getLogger(logger_name)
        logger.setLevel(root_level)
        logger.addHandler(_build_file_handler(filename, root_level))

    # Silence overly chatty third-party loggers.
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
