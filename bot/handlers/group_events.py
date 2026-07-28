# -*- coding: utf-8 -*-
"""
bot/handlers/group_events.py — Botning guruhlardagi a'zolik holatini kuzatish.

Bu router shaxsiy chat filtri qo'llanilmagan yagona joy — chunki
`my_chat_member` yangilanishlari faqat guruh/kanallarda yuz beradi.
Bot biror guruhda admin huquqini yo'qotsa yoki chiqarib yuborilsa,
tegishli guruh avtomatik ravishda NOFAOL qilinadi (ro'yxatdan
o'chirilmaydi — faqat is_active=False bo'ladi). Agar bot qaytadan
administrator qilib tayinlansa — guruh avtomatik qayta faollashadi.
"""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import ChatMemberUpdated

from bot.core.containers import ServiceContainer

logger = logging.getLogger(__name__)

router = Router(name="group_events")


@router.my_chat_member()
async def on_bot_membership_changed(event: ChatMemberUpdated, services: ServiceContainer) -> None:
    if event.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    new_status = event.new_chat_member.status
    chat_id = event.chat.id

    existing = await services.groups.get_by_chat_id(chat_id)
    if existing is None:
        # Guruh hali admin panel orqali ro'yxatga olinmagan bo'lsa hech
        # narsa qilinmaydi — guruhlar faqat admin tomonidan qo'lda qo'shiladi.
        return

    if new_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED, ChatMemberStatus.RESTRICTED):
        await services.groups.deactivate_by_chat_id(chat_id, reason=f"bot_status={new_status.value}")
        logger.warning("Bot guruhdan chiqarildi/cheklandi: chat_id=%s status=%s -> nofaol qilindi.", chat_id, new_status)
    elif new_status == ChatMemberStatus.MEMBER:
        await services.groups.deactivate_by_chat_id(chat_id, reason="not_admin_anymore")
        logger.warning("Bot guruhda admin huquqini yo'qotdi: chat_id=%s -> nofaol qilindi.", chat_id)
    elif new_status == ChatMemberStatus.ADMINISTRATOR:
        await services.groups.reactivate_by_chat_id(chat_id)
        logger.info("Bot guruhda admin: chat_id=%s -> qayta faollashtirildi.", chat_id)
