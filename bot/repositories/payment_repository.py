# -*- coding: utf-8 -*-
"""bot/repositories/payment_repository.py — Payment modeli uchun ma'lumotlar bazasi qatlami."""
from __future__ import annotations

import datetime as dt
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.payment import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        tariff_key: str,
        tariff_label: str,
        price: int,
        days: Optional[int],
        method: str,
        receipt_file_id: Optional[str] = None,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            tariff_key=tariff_key,
            tariff_label=tariff_label,
            price=price,
            days=days,
            method=method,
            status=PaymentStatus.PENDING.value,
            receipt_file_id=receipt_file_id,
            admin_notifications=[],
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get(self, payment_id: int) -> Optional[Payment]:
        return await self.session.get(Payment, payment_id)

    async def append_admin_notification(self, payment_id: int, admin_id: int, message_id: int) -> None:
        payment = await self.get(payment_id)
        if payment is None:
            return
        notifications = list(payment.admin_notifications or [])
        notifications.append({"admin_id": admin_id, "message_id": message_id})
        payment.admin_notifications = notifications
        await self.session.flush()

    async def decide(self, payment_id: int, status: str, decided_by: int, reject_reason: Optional[str] = None) -> Optional[Payment]:
        payment = await self.get(payment_id)
        if payment is None:
            return None
        payment.status = status
        payment.decided_by = decided_by
        payment.decided_at = dt.datetime.now(dt.timezone.utc)
        payment.reject_reason = reject_reason
        await self.session.flush()
        return payment

    async def list_by_status(self, status: str, offset: int = 0, limit: int = 10) -> Sequence[Payment]:
        result = await self.session.execute(
            select(Payment)
            .where(Payment.status == status)
            .order_by(Payment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_status(self, status: str) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Payment).where(Payment.status == status)
        )
        return result.scalar_one()
