# -*- coding: utf-8 -*-
"""bot/repositories/user_repository.py — User modeli uchun ma'lumotlar bazasi qatlami."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import SubscriptionStatus, User


class UserRepository:
    """Repository Pattern: barcha User bilan bog'liq SQL so'rovlar shu yerda."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, telegram_id: int) -> Optional[User]:
        return await self.session.get(User, telegram_id)

    async def get_or_create(self, telegram_id: int, username: Optional[str], full_name: Optional[str]) -> User:
        user = await self.get(telegram_id)
        if user is not None:
            changed = False
            if user.username != username:
                user.username = username
                changed = True
            if user.full_name != full_name:
                user.full_name = full_name
                changed = True
            if changed:
                await self.session.flush()
            return user

        user = User(telegram_id=telegram_id, username=username, full_name=full_name)
        self.session.add(user)
        await self.session.flush()
        return user

    async def save_phone(self, telegram_id: int, normalized_phone: str) -> None:
        user = await self.get(telegram_id)
        if user:
            user.phone_number = normalized_phone
            await self.session.flush()

    async def set_subscription(
        self,
        telegram_id: int,
        status: str,
        start=None,
        end=None,
        is_lifetime: bool = False,
    ) -> None:
        user = await self.get(telegram_id)
        if not user:
            return
        user.subscription_status = status
        user.subscription_start = start
        user.subscription_end = end
        user.subscription_is_lifetime = is_lifetime
        if status == SubscriptionStatus.ACTIVE.value:
            user.reminder_3day_sent = False
            user.reminder_1day_sent = False
        await self.session.flush()

    async def set_banned(self, telegram_id: int, banned: bool) -> None:
        user = await self.get(telegram_id)
        if user:
            user.is_banned = banned
            await self.session.flush()

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(User))
        return result.scalar_one()

    async def count_active_subscriptions(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.subscription_status == SubscriptionStatus.ACTIVE.value)
        )
        return result.scalar_one()

    async def list_paginated(self, offset: int = 0, limit: int = 10) -> Sequence[User]:
        result = await self.session.execute(
            select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def list_expiring_subscriptions(self) -> Sequence[User]:
        result = await self.session.execute(
            select(User).where(
                User.subscription_status == SubscriptionStatus.ACTIVE.value,
                User.subscription_is_lifetime.is_(False),
                User.subscription_end.is_not(None),
            )
        )
        return result.scalars().all()

    async def mark_reminder_sent(self, telegram_id: int, *, three_day: bool = False, one_day: bool = False) -> None:
        user = await self.get(telegram_id)
        if not user:
            return
        if three_day:
            user.reminder_3day_sent = True
        if one_day:
            user.reminder_1day_sent = True
        await self.session.flush()

    async def expire_subscription(self, telegram_id: int) -> None:
        user = await self.get(telegram_id)
        if user:
            user.subscription_status = SubscriptionStatus.EXPIRED.value
            await self.session.flush()
