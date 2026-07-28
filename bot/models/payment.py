# -*- coding: utf-8 -*-
"""
bot/models/payment.py — To'lov modeli.

Eski loyihadagi to'lov ish jarayoni (pending -> approved/rejected,
tarif asosida obuna muddati, admin bildirishnomalarini keyinchalik
tahrirlash) shu model va tegishli repository/service orqali
PostgreSQL ustida qayta qurilgan.
"""
from __future__ import annotations

import datetime as dt
import enum
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.base import Base, TimestampMixin


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PaymentMethod(str, enum.Enum):
    RECEIPT = "receipt"          # chek rasmi orqali
    CLICK = "click"
    PAYME = "payme"
    CONTACT_ADMIN = "contact_admin"


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"))

    tariff_key: Mapped[str] = mapped_column(String(50), nullable=False)
    tariff_label: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = lifetime

    method: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.PENDING.value, nullable=False)

    receipt_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Har bir adminga yuborilgan bildirishnoma xabar id'lari — keyinchalik
    # qaror chiqqach shu xabarlarni tahrirlash (edit) uchun saqlanadi.
    # Format: [{"admin_id": 123, "message_id": 456}, ...]
    admin_notifications: Mapped[List[dict]] = mapped_column(JSON, default=list, nullable=False)

    decided_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    reject_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    user: Mapped["User"] = relationship(back_populates="payments")
