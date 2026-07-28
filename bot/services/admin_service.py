# -*- coding: utf-8 -*-
"""bot/services/admin_service.py — Admin panel uchun statistikalar va sozlamalar."""
from __future__ import annotations

from dataclasses import dataclass

from bot.config import settings
from bot.models.advertisement import AdStatus
from bot.models.payment import PaymentStatus
from bot.repositories import (
    AdminSettingRepository,
    AdvertisementRepository,
    GroupRepository,
    PaymentRepository,
    UserRepository,
)

SETTING_CONCURRENCY = "send_concurrency_limit"
SETTING_GROUP_CHECK_HOURS = "group_validation_interval_hours"
SETTING_AUTO_STOP_HOURS = "ad_auto_stop_hours"


@dataclass
class BotStatistics:
    total_users: int
    active_subs: int
    active_ads: int
    stopped_ads: int
    active_groups: int
    pending_payments: int
    approved_payments: int


class AdminService:
    def __init__(
        self,
        user_repo: UserRepository,
        ad_repo: AdvertisementRepository,
        group_repo: GroupRepository,
        payment_repo: PaymentRepository,
        setting_repo: AdminSettingRepository,
    ):
        self.user_repo = user_repo
        self.ad_repo = ad_repo
        self.group_repo = group_repo
        self.payment_repo = payment_repo
        self.setting_repo = setting_repo

    async def get_statistics(self) -> BotStatistics:
        return BotStatistics(
            total_users=await self.user_repo.count_all(),
            active_subs=await self.user_repo.count_active_subscriptions(),
            active_ads=await self.ad_repo.count_by_status(AdStatus.ACTIVE.value),
            stopped_ads=await self.ad_repo.count_by_status(AdStatus.STOPPED.value),
            active_groups=await self.group_repo.count_active(),
            pending_payments=await self.payment_repo.count_by_status(PaymentStatus.PENDING.value),
            approved_payments=await self.payment_repo.count_by_status(PaymentStatus.APPROVED.value),
        )

    async def get_effective_settings(self) -> dict:
        stored = await self.setting_repo.get_all()
        return {
            "concurrency": int(stored.get(SETTING_CONCURRENCY, settings.send_concurrency_limit)),
            "group_check_hours": int(stored.get(SETTING_GROUP_CHECK_HOURS, settings.group_validation_interval_hours)),
            "auto_stop_hours": int(stored.get(SETTING_AUTO_STOP_HOURS, settings.ad_auto_stop_hours)),
        }
