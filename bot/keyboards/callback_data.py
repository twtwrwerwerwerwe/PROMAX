# -*- coding: utf-8 -*-
"""
bot/keyboards/callback_data.py — Aiogram 3 CallbackData factory klasslari.

Type-safe callback_data ishlatish orqali:
  * noto'g'ri/eskirgan callbacklarni avtomatik rad etish osonlashadi,
  * har doim aniq maydonlar (masalan ad_id) bilan ishlaymiz — qo'lda
    string split qilish va undan kelib chiqadigan xatoliklar yo'q bo'ladi.
"""
from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class ContinueCB(CallbackData, prefix="cont"):
    pass


class TariffCB(CallbackData, prefix="trf"):
    tariff_key: str


class PayMethodCB(CallbackData, prefix="pm"):
    tariff_key: str
    method: str


class ReceiptBackCB(CallbackData, prefix="rcb"):
    pass


class IntervalCB(CallbackData, prefix="intv"):
    minutes: int
    context: str  # "create" | "edit" | "edit_both"


class ConfirmAdCB(CallbackData, prefix="cfad"):
    action: str  # "start" | "cancel"


class AdPanelCB(CallbackData, prefix="adp"):
    ad_id: int
    action: str  # "pause" | "resume" | "edit" | "stop"


class EditChoiceCB(CallbackData, prefix="edc"):
    ad_id: int
    field: str  # "text" | "interval" | "both" | "back"


class AdminMenuCB(CallbackData, prefix="am"):
    section: str


class AdminPaymentActionCB(CallbackData, prefix="apa"):
    payment_id: int
    action: str  # "approve" | "reject"


class AdminPaymentListCB(CallbackData, prefix="apl"):
    status: str
    offset: int


class AdminUserActionCB(CallbackData, prefix="aua"):
    user_id: int
    action: str  # "ban" | "unban"


class AdminUserListCB(CallbackData, prefix="aul"):
    offset: int


class AdminAdActionCB(CallbackData, prefix="ada"):
    ad_id: int
    action: str  # "force_stop"


class AdminAdListCB(CallbackData, prefix="adl"):
    status: str
    offset: int


class AdminGroupMenuCB(CallbackData, prefix="agm"):
    action: str  # "add" | "list" | "delete" | "refresh" | "back"


class AdminGroupListCB(CallbackData, prefix="agl"):
    offset: int


class AdminGroupDeleteCB(CallbackData, prefix="agd"):
    group_id: int
    confirm: str  # "ask" | "yes" | "no"
