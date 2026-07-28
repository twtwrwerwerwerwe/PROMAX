# -*- coding: utf-8 -*-
"""
bot/core/containers.py — Dependency Injection konteyneri.

Har bir update uchun bitta AsyncSession ochiladi va shu session asosida
barcha repository/service obyektlari shu yerda yig'iladi. Handlerlar
to'g'ridan-to'g'ri SQLAlchemy yoki repository bilan ishlamaydi — faqat
shu konteyner orqali service qatlamiga murojaat qiladi.
"""
from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories import (
    AdminSettingRepository,
    AdvertisementRepository,
    GroupRepository,
    PaymentRepository,
    UserRepository,
)
from bot.services import (
    AdminService,
    AdvertisementService,
    GroupService,
    PaymentService,
    UserService,
)


@dataclass
class ServiceContainer:
    session: AsyncSession
    users: UserService
    payments: PaymentService
    advertisements: AdvertisementService
    groups: GroupService
    admin: AdminService

    @classmethod
    def build(cls, session: AsyncSession, bot: Bot) -> "ServiceContainer":
        user_repo = UserRepository(session)
        payment_repo = PaymentRepository(session)
        ad_repo = AdvertisementRepository(session)
        group_repo = GroupRepository(session)
        setting_repo = AdminSettingRepository(session)

        return cls(
            session=session,
            users=UserService(user_repo),
            payments=PaymentService(user_repo, payment_repo),
            advertisements=AdvertisementService(ad_repo),
            groups=GroupService(group_repo, bot),
            admin=AdminService(user_repo, ad_repo, group_repo, payment_repo, setting_repo),
        )
