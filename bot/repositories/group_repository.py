# -*- coding: utf-8 -*-
"""bot/repositories/group_repository.py — Group modeli uchun DB qatlami."""
from __future__ import annotations

import datetime as dt
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.group import Group


class GroupRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, group_id: int) -> Optional[Group]:
        return await self.session.get(Group, group_id)

    async def get_by_chat_id(self, chat_id: int) -> Optional[Group]:
        result = await self.session.execute(select(Group).where(Group.chat_id == chat_id))
        return result.scalars().first()

    async def create(self, chat_id: int, title: Optional[str], added_by: Optional[int]) -> Group:
        group = Group(chat_id=chat_id, title=title, is_active=True, added_by=added_by,
                       last_verified_at=dt.datetime.now(dt.timezone.utc))
        self.session.add(group)
        await self.session.flush()
        return group

    async def delete(self, group_id: int) -> bool:
        group = await self.get(group_id)
        if group is None:
            return False
        await self.session.delete(group)
        await self.session.flush()
        return True

    async def set_active(self, chat_id: int, active: bool, error: Optional[str] = None) -> None:
        group = await self.get_by_chat_id(chat_id)
        if group is None:
            return
        group.is_active = active
        group.last_verified_at = dt.datetime.now(dt.timezone.utc)
        group.last_error = error
        await self.session.flush()

    async def list_active(self) -> Sequence[Group]:
        result = await self.session.execute(select(Group).where(Group.is_active.is_(True)))
        return result.scalars().all()

    async def list_all(self, offset: int = 0, limit: int = 20) -> Sequence[Group]:
        result = await self.session.execute(
            select(Group).order_by(Group.created_at.desc()).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def count_active(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Group).where(Group.is_active.is_(True))
        )
        return result.scalar_one()

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(Group))
        return result.scalar_one()
