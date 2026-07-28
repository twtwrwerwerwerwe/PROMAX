# -*- coding: utf-8 -*-
"""bot/repositories/admin_setting_repository.py — AdminSetting modeli uchun DB qatlami."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.admin_setting import AdminSetting


class AdminSettingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str) -> Optional[str]:
        setting = await self.session.get(AdminSetting, key)
        return setting.value if setting else None

    async def set(self, key: str, value: str) -> None:
        setting = await self.session.get(AdminSetting, key)
        if setting is None:
            setting = AdminSetting(key=key, value=value)
            self.session.add(setting)
        else:
            setting.value = value
        await self.session.flush()

    async def get_all(self) -> dict:
        result = await self.session.execute(select(AdminSetting))
        return {row.key: row.value for row in result.scalars().all()}
