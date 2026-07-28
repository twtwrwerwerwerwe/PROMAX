# -*- coding: utf-8 -*-
"""bot/repositories/advertisement_repository.py — Advertisement modeli uchun DB qatlami."""
from __future__ import annotations

import datetime as dt
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.advertisement import AdStatus, Advertisement


class AdvertisementRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, ad_id: int) -> Optional[Advertisement]:
        return await self.session.get(Advertisement, ad_id)

    async def get_active_for_user(self, user_id: int) -> Optional[Advertisement]:
        result = await self.session.execute(
            select(Advertisement).where(
                Advertisement.user_id == user_id,
                Advertisement.status.in_([AdStatus.ACTIVE.value, AdStatus.PAUSED.value]),
            )
        )
        return result.scalars().first()

    async def create(self, user_id: int, text: str, interval_minutes: int) -> Advertisement:
        ad = Advertisement(
            user_id=user_id,
            text=text,
            interval_minutes=interval_minutes,
            status=AdStatus.CREATED.value,
        )
        self.session.add(ad)
        await self.session.flush()
        return ad

    async def activate(self, ad_id: int, auto_stop_hours: int) -> Optional[Advertisement]:
        ad = await self.get(ad_id)
        if ad is None:
            return None
        now = dt.datetime.now(dt.timezone.utc)
        ad.status = AdStatus.ACTIVE.value
        ad.started_at = now
        ad.expires_at = now + dt.timedelta(hours=auto_stop_hours)
        await self.session.flush()
        return ad

    async def set_status(self, ad_id: int, status: str) -> Optional[Advertisement]:
        ad = await self.get(ad_id)
        if ad is None:
            return None
        ad.status = status
        if status == AdStatus.STOPPED.value:
            ad.stopped_at = dt.datetime.now(dt.timezone.utc)
        await self.session.flush()
        return ad

    async def update_text(self, ad_id: int, text: str) -> Optional[Advertisement]:
        ad = await self.get(ad_id)
        if ad is None:
            return None
        ad.text = text
        await self.session.flush()
        return ad

    async def update_interval(self, ad_id: int, interval_minutes: int) -> Optional[Advertisement]:
        ad = await self.get(ad_id)
        if ad is None:
            return None
        ad.interval_minutes = interval_minutes
        await self.session.flush()
        return ad

    async def register_sent(self, ad_id: int) -> None:
        ad = await self.get(ad_id)
        if ad is None:
            return
        ad.total_sent_count += 1
        ad.last_sent_at = dt.datetime.now(dt.timezone.utc)
        await self.session.flush()

    async def list_all_active(self) -> Sequence[Advertisement]:
        """Recovery uchun — bot qayta ishga tushganda barcha ACTIVE e'lonlarni qaytaradi."""
        result = await self.session.execute(
            select(Advertisement).where(Advertisement.status == AdStatus.ACTIVE.value)
        )
        return result.scalars().all()

    async def list_by_status(self, status: str, offset: int = 0, limit: int = 10) -> Sequence[Advertisement]:
        result = await self.session.execute(
            select(Advertisement)
            .where(Advertisement.status == status)
            .order_by(Advertisement.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_status(self, status: str) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Advertisement).where(Advertisement.status == status)
        )
        return result.scalar_one()
