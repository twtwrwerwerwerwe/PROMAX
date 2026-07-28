# -*- coding: utf-8 -*-
"""
bot/config.py — Markazlashtirilgan konfiguratsiya klassi.

Barcha muhit o'zgaruvchilari (environment variables) shu yerda, bitta
joyda o'qiladi va tekshiriladi. Boshqa hech qanday modul ".env" faylini
to'g'ridan-to'g'ri o'qimaydi — barchasi shu `Settings` obyekti orqali
ishlaydi (Dependency Injection uchun qulay, test qilish uchun ham oson).
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Dict, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import sys

__all__ = ["Settings", "get_settings", "settings"]


class Tariff(dict):
    """Lightweight typed-access wrapper around a tariff dict."""

    @property
    def label(self) -> str:
        return self["label"]

    @property
    def days(self) -> Optional[int]:
        return self.get("days")

    @property
    def price(self) -> int:
        return self["price"]


class Settings(BaseSettings):
    """Application-wide settings, populated from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ---------- Bot ----------
    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str = Field(default="", alias="BOT_USERNAME")

    # ---------- Admin ----------
    admin_ids_raw: str = Field(default="", alias="ADMIN_IDS")
    admin_name: str = Field(default="Administrator", alias="ADMIN_NAME")
    admin_phone: str = Field(default="", alias="ADMIN_PHONE")
    admin_profile_url: str = Field(default="", alias="ADMIN_PROFILE_URL")

    # ---------- Database ----------
    database_url: str = Field(alias="DATABASE_URL")

    # ---------- Redis ----------
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # ---------- Logging ----------
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: str = Field(default="logs", alias="LOG_DIR")

    # ---------- Timezone ----------
    timezone: str = Field(default="Asia/Tashkent", alias="TIMEZONE")

    # ---------- Tariffs ----------
    tariffs_json: str = Field(default="{}", alias="TARIFFS_JSON")

    # ---------- Receipt payment card ----------
    payment_card_number: str = Field(default="", alias="PAYMENT_CARD_NUMBER")
    payment_card_owner: str = Field(default="", alias="PAYMENT_CARD_OWNER")
    payment_card_phone: str = Field(default="", alias="PAYMENT_CARD_PHONE")

    # ---------- Click / Payme ----------
    click_merchant_id: Optional[str] = Field(default=None, alias="CLICK_MERCHANT_ID")
    payme_merchant_id: Optional[str] = Field(default=None, alias="PAYME_MERCHANT_ID")

    # ---------- Advertisement engine ----------
    ad_intervals_raw: str = Field(default="5,10,15,20", alias="AD_INTERVALS")
    ad_auto_stop_hours: int = Field(default=24, alias="AD_AUTO_STOP_HOURS")
    send_concurrency_limit: int = Field(default=20, alias="SEND_CONCURRENCY_LIMIT")
    flood_wait_max_retries: int = Field(default=5, alias="FLOOD_WAIT_MAX_RETRIES")

    # ---------- Subscription watcher ----------
    subscription_reminder_days_before: int = Field(default=3, alias="SUBSCRIPTION_REMINDER_DAYS_BEFORE")
    background_loop_interval_seconds: int = Field(default=30, alias="BACKGROUND_LOOP_INTERVAL_SECONDS")

    # ---------- Group validation ----------
    group_validation_interval_hours: int = Field(default=6, alias="GROUP_VALIDATION_INTERVAL_HOURS")

    # ------------------------------------------------------------------
    # Derived / parsed properties
    # ------------------------------------------------------------------
    @property
    def admin_ids(self) -> List[int]:
        if not self.admin_ids_raw:
            return []
        return [int(x.strip()) for x in self.admin_ids_raw.split(",") if x.strip()]

    @property
    def ad_intervals(self) -> List[int]:
        return [int(x.strip()) for x in self.ad_intervals_raw.split(",") if x.strip()]

    @property
    def tariffs(self) -> Dict[str, Tariff]:
        raw = json.loads(self.tariffs_json)
        return {k: Tariff(v) for k, v in raw.items()}

    @property
    def payment_card(self) -> Dict[str, str]:
        return {
            "number": self.payment_card_number,
            "owner": self.payment_card_owner,
            "phone": self.payment_card_phone,
        }


@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton Settings instance."""
    return Settings()


try:
    settings = get_settings()
except Exception as exc:  # pragma: no cover - startup/runtime guard
    sys.stderr.write(
        "Fatal: failed to load Settings — required environment variables may be missing.\n"
    )
    sys.stderr.write(
        "Make sure `BOT_TOKEN` and `DATABASE_URL` are set in the environment or provided in a .env file.\n"
    )
    sys.stderr.write(f"Detailed error: {exc}\n")
    # Exit early with non-zero code so the container logs show a clear reason
    raise
