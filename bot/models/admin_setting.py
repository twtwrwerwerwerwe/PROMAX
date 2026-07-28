# -*- coding: utf-8 -*-
"""bot/models/admin_setting.py — Admin panel orqali o'zgartiriladigan sozlamalar."""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.base import Base, TimestampMixin


class AdminSetting(TimestampMixin, Base):
    __tablename__ = "admin_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(1000), nullable=False)
