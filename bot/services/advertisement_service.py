# -*- coding: utf-8 -*-
"""bot/services/advertisement_service.py — E'lon (reklama) biznes-logikasi."""
from __future__ import annotations

import logging
from typing import List, Optional

from bot.config import settings
from bot.exceptions import (
    AdvertisementAlreadyActiveError,
    AdvertisementNotFoundError,
    AdvertisementOwnershipError,
)
from bot.models.advertisement import AdStatus, Advertisement
from bot.repositories import AdvertisementRepository

logger = logging.getLogger(__name__)

MAX_AD_TEXT_LENGTH = 3500


class AdvertisementService:
    def __init__(self, ad_repo: AdvertisementRepository):
        self.ad_repo = ad_repo

    async def get_active_or_paused_for_user(self, user_id: int) -> Optional[Advertisement]:
        return await self.ad_repo.get_active_for_user(user_id)

    async def create_draft(self, user_id: int, text: str, interval_minutes: int) -> Advertisement:
        existing = await self.ad_repo.get_active_for_user(user_id)
        if existing is not None:
            raise AdvertisementAlreadyActiveError(f"User {user_id} already has an active advertisement")
        if interval_minutes not in settings.ad_intervals:
            raise ValueError("Invalid interval")
        return await self.ad_repo.create(user_id=user_id, text=text, interval_minutes=interval_minutes)

    async def activate(self, ad_id: int, user_id: int) -> Advertisement:
        ad = await self._get_owned(ad_id, user_id)
        ad = await self.ad_repo.activate(ad_id, settings.ad_auto_stop_hours)
        logger.info("Ad #%s activated for user=%s", ad_id, user_id)
        return ad

    async def pause(self, ad_id: int, user_id: int) -> Advertisement:
        ad = await self._get_owned(ad_id, user_id)
        if ad.status != AdStatus.ACTIVE.value:
            raise ValueError("Only an ACTIVE advertisement can be paused")
        result = await self.ad_repo.set_status(ad_id, AdStatus.PAUSED.value)
        logger.info("Ad #%s paused by user=%s", ad_id, user_id)
        return result

    async def resume(self, ad_id: int, user_id: int) -> Advertisement:
        ad = await self._get_owned(ad_id, user_id)
        if ad.status != AdStatus.PAUSED.value:
            raise ValueError("Only a PAUSED advertisement can be resumed")
        result = await self.ad_repo.set_status(ad_id, AdStatus.ACTIVE.value)
        logger.info("Ad #%s resumed by user=%s", ad_id, user_id)
        return result

    async def stop(self, ad_id: int, user_id: Optional[int] = None) -> Advertisement:
        """user_id=None bo'lsa — admin majburiy to'xtatuvi (ownership tekshiruvisiz)."""
        if user_id is not None:
            await self._get_owned(ad_id, user_id)
        result = await self.ad_repo.set_status(ad_id, AdStatus.STOPPED.value)
        logger.info("Ad #%s stopped (user=%s)", ad_id, user_id)
        return result

    async def update_text(self, ad_id: int, user_id: int, new_text: str) -> Advertisement:
        await self._get_owned(ad_id, user_id)
        return await self.ad_repo.update_text(ad_id, new_text)

    async def update_interval(self, ad_id: int, user_id: int, new_interval: int) -> Advertisement:
        await self._get_owned(ad_id, user_id)
        if new_interval not in settings.ad_intervals:
            raise ValueError("Invalid interval")
        return await self.ad_repo.update_interval(ad_id, new_interval)

    async def register_sent(self, ad_id: int) -> None:
        await self.ad_repo.register_sent(ad_id)

    async def get(self, ad_id: int) -> Optional[Advertisement]:
        return await self.ad_repo.get(ad_id)

    async def list_all_active(self) -> List[Advertisement]:
        return list(await self.ad_repo.list_all_active())

    async def list_by_status(self, status: str, offset: int = 0, limit: int = 10) -> List[Advertisement]:
        return list(await self.ad_repo.list_by_status(status, offset, limit))

    async def count_by_status(self, status: str) -> int:
        return await self.ad_repo.count_by_status(status)

    async def _get_owned(self, ad_id: int, user_id: int) -> Advertisement:
        ad = await self.ad_repo.get(ad_id)
        if ad is None:
            raise AdvertisementNotFoundError(str(ad_id))
        if ad.user_id != user_id:
            raise AdvertisementOwnershipError(f"user={user_id} does not own ad={ad_id}")
        return ad

    @staticmethod
    def validate_text(text: str) -> None:
        if not text or not text.strip():
            raise ValueError("empty")
        if len(text) > MAX_AD_TEXT_LENGTH:
            raise ValueError("too_long")
