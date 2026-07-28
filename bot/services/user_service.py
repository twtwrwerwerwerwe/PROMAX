# -*- coding: utf-8 -*-
"""bot/services/user_service.py — Foydalanuvchi bilan bog'liq biznes-logika."""
from __future__ import annotations

from typing import List, Optional

from bot.exceptions import InvalidPhoneNumberError
from bot.models.user import User
from bot.repositories import UserRepository
from bot.utils.phone import normalize_phone


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_or_create(self, telegram_id: int, username: Optional[str], full_name: Optional[str]) -> User:
        return await self.user_repo.get_or_create(telegram_id, username, full_name)

    async def get(self, telegram_id: int) -> Optional[User]:
        return await self.user_repo.get(telegram_id)

    async def save_phone(self, telegram_id: int, raw_phone: str) -> str:
        normalized = normalize_phone(raw_phone)
        if normalized is None:
            raise InvalidPhoneNumberError(raw_phone)
        await self.user_repo.save_phone(telegram_id, normalized)
        return normalized

    async def has_phone(self, telegram_id: int) -> bool:
        user = await self.user_repo.get(telegram_id)
        return bool(user and user.phone_number)

    async def is_banned(self, telegram_id: int) -> bool:
        user = await self.user_repo.get(telegram_id)
        return bool(user and user.is_banned)

    async def set_banned(self, telegram_id: int, banned: bool) -> None:
        await self.user_repo.set_banned(telegram_id, banned)

    async def list_paginated(self, offset: int = 0, limit: int = 10) -> List[User]:
        return list(await self.user_repo.list_paginated(offset, limit))

    async def count_all(self) -> int:
        return await self.user_repo.count_all()

    async def count_active_subscriptions(self) -> int:
        return await self.user_repo.count_active_subscriptions()
