# -*- coding: utf-8 -*-
"""
bot/services/payment_service.py — To'lov tizimi biznes-logikasi.

Bu modul eski loyihadagi `handlers/payment.py` va `handlers/payment_admin.py`
ichidagi ish jarayonining PORTI hisoblanadi:

    * tarif tanlash -> to'lov usuli tanlash -> chek/karta/admin bilan bog'lanish
    * har bir adminga bildirishnoma yuborish va keyinchalik ularni edit qilish
    * pending -> approved/rejected holat almashinuvi, ikki marta qayta ishlashdan
      himoyalangan (idempotent) tasdiqlash/rad etish
    * tarifga qarab obuna muddatini hisoblash (kunlar yoki umrbod)

Faqat texnik qatlam (aiogram2 -> aiogram3, JSON fayl -> PostgreSQL) almashtirilgan,
ish jarayonining o'zi eski loyihadagidek saqlangan.
"""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from typing import List, Optional

from bot.config import Tariff, settings
from bot.exceptions import PaymentAlreadyProcessedError
from bot.models.payment import Payment, PaymentStatus
from bot.models.user import SubscriptionStatus
from bot.repositories import PaymentRepository, UserRepository

logger = logging.getLogger("payment")


@dataclass
class TariffChoice:
    key: str
    tariff: Tariff


class PaymentService:
    def __init__(self, user_repo: UserRepository, payment_repo: PaymentRepository):
        self.user_repo = user_repo
        self.payment_repo = payment_repo

    # ------------------------------------------------------------------
    # Tariffs
    # ------------------------------------------------------------------
    def list_tariffs(self) -> List[TariffChoice]:
        return [TariffChoice(key=key, tariff=tariff) for key, tariff in settings.tariffs.items()]

    def get_tariff(self, key: str) -> Optional[Tariff]:
        return settings.tariffs.get(key)

    # ------------------------------------------------------------------
    # Creating a payment request (mirrors old handlers/payment.py flow)
    # ------------------------------------------------------------------
    async def create_payment_request(
        self,
        user_id: int,
        tariff_key: str,
        method: str,
        receipt_file_id: Optional[str] = None,
    ) -> Payment:
        tariff = self.get_tariff(tariff_key)
        if tariff is None:
            raise ValueError(f"Unknown tariff key: {tariff_key}")

        payment = await self.payment_repo.create(
            user_id=user_id,
            tariff_key=tariff_key,
            tariff_label=tariff.label,
            price=tariff.price,
            days=tariff.days,
            method=method,
            receipt_file_id=receipt_file_id,
        )
        logger.info("Payment #%s yaratildi: user=%s tariff=%s method=%s", payment.id, user_id, tariff_key, method)
        return payment

    async def register_admin_notification(self, payment_id: int, admin_id: int, message_id: int) -> None:
        await self.payment_repo.append_admin_notification(payment_id, admin_id, message_id)

    # ------------------------------------------------------------------
    # Approve / Reject (mirrors old handlers/payment_admin.py, with the
    # same idempotency guard against double-processing).
    # ------------------------------------------------------------------
    async def approve_payment(self, payment_id: int, admin_id: int) -> Payment:
        payment = await self.payment_repo.get(payment_id)
        if payment is None:
            raise ValueError("Payment not found")
        if payment.status != PaymentStatus.PENDING.value:
            raise PaymentAlreadyProcessedError(f"Payment #{payment_id} already {payment.status}")

        payment = await self.payment_repo.decide(payment_id, PaymentStatus.APPROVED.value, admin_id)

        now = dt.datetime.now(dt.timezone.utc)
        is_lifetime = payment.days is None
        end = None if is_lifetime else now + dt.timedelta(days=payment.days)

        await self.user_repo.set_subscription(
            telegram_id=payment.user_id,
            status=SubscriptionStatus.ACTIVE.value,
            start=now,
            end=end,
            is_lifetime=is_lifetime,
        )
        logger.info("Payment #%s admin=%s tomonidan TASDIQLANDI (user=%s)", payment_id, admin_id, payment.user_id)
        return payment

    async def reject_payment(self, payment_id: int, admin_id: int, reason: str) -> Payment:
        payment = await self.payment_repo.get(payment_id)
        if payment is None:
            raise ValueError("Payment not found")
        if payment.status != PaymentStatus.PENDING.value:
            raise PaymentAlreadyProcessedError(f"Payment #{payment_id} already {payment.status}")

        payment = await self.payment_repo.decide(payment_id, PaymentStatus.REJECTED.value, admin_id, reason)
        await self.user_repo.set_subscription(telegram_id=payment.user_id, status=SubscriptionStatus.REJECTED.value)
        logger.info("Payment #%s admin=%s tomonidan RAD ETILDI (user=%s) sabab=%s", payment_id, admin_id, payment.user_id, reason)
        return payment

    async def get_payment(self, payment_id: int) -> Optional[Payment]:
        return await self.payment_repo.get(payment_id)

    async def list_pending(self, offset: int = 0, limit: int = 10) -> List[Payment]:
        return list(await self.payment_repo.list_by_status(PaymentStatus.PENDING.value, offset, limit))

    async def list_by_status(self, status: str, offset: int = 0, limit: int = 10) -> List[Payment]:
        return list(await self.payment_repo.list_by_status(status, offset, limit))

    async def count_pending(self) -> int:
        return await self.payment_repo.count_by_status(PaymentStatus.PENDING.value)

    async def count_approved(self) -> int:
        return await self.payment_repo.count_by_status(PaymentStatus.APPROVED.value)
