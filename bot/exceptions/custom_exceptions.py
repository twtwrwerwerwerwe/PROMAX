# -*- coding: utf-8 -*-
"""bot/exceptions/custom_exceptions.py — Loyihaga xos maxsus xatoliklar."""
from __future__ import annotations


class BotBaseException(Exception):
    """Barcha maxsus xatoliklar uchun asosiy klass."""


class InvalidPhoneNumberError(BotBaseException):
    """Telefon raqami noto'g'ri formatda bo'lsa."""


class SubscriptionRequiredError(BotBaseException):
    """Foydalanuvchida faol obuna bo'lmasa."""


class AdvertisementAlreadyActiveError(BotBaseException):
    """Foydalanuvchida allaqachon faol e'lon bo'lsa."""


class AdvertisementNotFoundError(BotBaseException):
    """E'lon topilmasa."""


class AdvertisementOwnershipError(BotBaseException):
    """Foydalanuvchi boshqa birovning e'loniga aralashmoqchi bo'lsa."""


class PaymentAlreadyProcessedError(BotBaseException):
    """To'lov allaqachon tasdiqlangan/rad etilgan bo'lsa (double-processing himoyasi)."""


class GroupValidationError(BotBaseException):
    """Guruhni qo'shishda tekshiruv muvaffaqiyatsiz tugasa."""

    def __init__(self, message: str, code: str = "unknown"):
        super().__init__(message)
        self.code = code


class SchedulerJobAlreadyRunningError(BotBaseException):
    """Bitta reklama uchun ikkinchi marta scheduler ishga tushirilmoqchi bo'lsa."""
