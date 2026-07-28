# -*- coding: utf-8 -*-
"""bot/models/user.py — Foydalanuvchi (haydovchi) modeli."""
from __future__ import annotations

import datetime as dt
import enum
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.base import Base, TimestampMixin


class SubscriptionStatus(str, enum.Enum):
    """Foydalanuvchining to'lov/obuna holati."""
    NONE = "none"               # hali hech qanday to'lov qilmagan
    PENDING = "pending"         # to'lov admin tasdig'ini kutmoqda
    ACTIVE = "active"           # obuna faol
    EXPIRED = "expired"         # obuna muddati tugagan
    REJECTED = "rejected"       # so'nggi to'lov rad etilgan


class User(TimestampMixin, Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    subscription_status: Mapped[str] = mapped_column(
        String(20), default=SubscriptionStatus.NONE.value, nullable=False
    )
    subscription_start: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    subscription_end: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    subscription_is_lifetime: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    reminder_3day_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_1day_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    payments: Mapped[List["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    advertisements: Mapped[List["Advertisement"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def has_active_subscription(self) -> bool:
        if self.subscription_status != SubscriptionStatus.ACTIVE.value:
            return False
        if self.subscription_is_lifetime:
            return True
        if self.subscription_end is None:
            return False
        now = dt.datetime.now(dt.timezone.utc)
        end = self.subscription_end
        if end.tzinfo is None:
            end = end.replace(tzinfo=dt.timezone.utc)
        return end > now

    @property
    def display_name(self) -> str:
        return self.full_name or (f"@{self.username}" if self.username else str(self.telegram_id))
