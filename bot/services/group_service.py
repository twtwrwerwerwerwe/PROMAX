# -*- coding: utf-8 -*-
"""bot/services/group_service.py — Guruhlarni boshqarish biznes-logikasi."""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from aiogram import Bot
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError

from bot.exceptions import GroupValidationError
from bot.models.group import Group
from bot.repositories import GroupRepository

logger = logging.getLogger(__name__)


class GroupService:
    def __init__(self, group_repo: GroupRepository, bot: Bot):
        self.group_repo = group_repo
        self.bot = bot

    async def _validate_chat(self, chat_id: int) -> Tuple[str, bool]:
        """Chat mavjudligini, guruh ekanligini va bot admin ekanligini tekshiradi.

        Returns (title, is_valid). Xatolik bo'lsa GroupValidationError ko'taradi.
        """
        try:
            chat = await self.bot.get_chat(chat_id)
        except TelegramForbiddenError:
            raise GroupValidationError("Bot bu guruhdan chiqarib yuborilgan yoki kira olmaydi.", code="not_found")
        except TelegramBadRequest:
            raise GroupValidationError("Guruh topilmadi.", code="not_found")
        except TelegramAPIError as exc:
            raise GroupValidationError(f"Telegram xatoligi: {exc}", code="api_error")

        if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
            raise GroupValidationError("Berilgan ID guruh emas.", code="not_a_group")

        try:
            member = await self.bot.get_chat_member(chat_id, self.bot.id)
        except TelegramAPIError as exc:
            raise GroupValidationError(f"Bot holatini tekshirib bo'lmadi: {exc}", code="api_error")

        if member.status != ChatMemberStatus.ADMINISTRATOR:
            raise GroupValidationError("Bot ushbu guruhda administrator emas.", code="not_admin")

        return chat.title or str(chat_id), True

    async def add_group(self, chat_id: int, added_by: int) -> Group:
        existing = await self.group_repo.get_by_chat_id(chat_id)
        if existing is not None:
            if existing.is_active:
                raise GroupValidationError("Ushbu guruh allaqachon ro'yxatda mavjud.", code="already_exists")
            # Reactivate a previously-deactivated group after re-verification.
            title, _ = await self._validate_chat(chat_id)
            await self.group_repo.set_active(chat_id, True)
            return existing

        title, _ = await self._validate_chat(chat_id)
        return await self.group_repo.create(chat_id=chat_id, title=title, added_by=added_by)

    async def delete_group(self, group_id: int) -> bool:
        return await self.group_repo.delete(group_id)

    async def list_active(self) -> List[Group]:
        return list(await self.group_repo.list_active())

    async def list_all(self, offset: int = 0, limit: int = 20) -> List[Group]:
        return list(await self.group_repo.list_all(offset, limit))

    async def count_active(self) -> int:
        return await self.group_repo.count_active()

    async def count_all(self) -> int:
        return await self.group_repo.count_all()

    async def get(self, group_id: int) -> Optional[Group]:
        return await self.group_repo.get(group_id)

    async def get_by_chat_id(self, chat_id: int):
        return await self.group_repo.get_by_chat_id(chat_id)

    async def deactivate_by_chat_id(self, chat_id: int, reason: str) -> None:
        await self.group_repo.set_active(chat_id, False, error=reason)

    async def reactivate_by_chat_id(self, chat_id: int) -> None:
        await self.group_repo.set_active(chat_id, True)

    async def revalidate_all(self) -> None:
        """Barcha ACTIVE guruhlarni davriy ravishda tekshiradi.

        Agar bot admin huquqini yo'qotgan bo'lsa — guruhni o'chirmasdan,
        faqat NOFAOL deb belgilaydi.
        """
        groups = await self.group_repo.list_active()
        for group in groups:
            try:
                await self._validate_chat(group.chat_id)
            except GroupValidationError as exc:
                logger.warning("Guruh %s (%s) endi yaroqsiz: %s", group.chat_id, group.title, exc)
                await self.group_repo.set_active(group.chat_id, False, error=str(exc))
            else:
                await self.group_repo.set_active(group.chat_id, True)
