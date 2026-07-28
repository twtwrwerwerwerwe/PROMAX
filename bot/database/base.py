# -*- coding: utf-8 -*-
"""bot/database/base.py — Declarative base va umumiy mixinlar."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Barcha ORM modellari uchun asosiy klass."""
    pass


class TimestampMixin:
    """created_at / updated_at ustunlarini avtomatik qo'shadi."""

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
