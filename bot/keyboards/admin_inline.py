# -*- coding: utf-8 -*-
"""bot/keyboards/admin_inline.py — Admin panel uchun inline klaviaturalar."""
from __future__ import annotations

from typing import Sequence

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.callback_data import (
    AdminAdActionCB,
    AdminAdListCB,
    AdminGroupDeleteCB,
    AdminGroupListCB,
    AdminGroupMenuCB,
    AdminMenuCB,
    AdminPaymentActionCB,
    AdminPaymentListCB,
    AdminUserActionCB,
    AdminUserListCB,
)
from bot.models.advertisement import Advertisement
from bot.models.group import Group
from bot.models.payment import Payment
from bot.models.user import User
from bot.utils.text_templates import T


def admin_root_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=T.BTN_ADMIN_STATS, callback_data=AdminMenuCB(section="stats"))
    builder.button(text=T.BTN_ADMIN_USERS, callback_data=AdminMenuCB(section="users"))
    builder.button(text=T.BTN_ADMIN_PAYMENTS, callback_data=AdminMenuCB(section="payments"))
    builder.button(text=T.BTN_ADMIN_ACTIVE_ADS, callback_data=AdminMenuCB(section="active_ads"))
    builder.button(text=T.BTN_ADMIN_STOPPED_ADS, callback_data=AdminMenuCB(section="stopped_ads"))
    builder.button(text=T.BTN_ADMIN_GROUPS, callback_data=AdminMenuCB(section="groups"))
    builder.button(text=T.BTN_ADMIN_SETTINGS, callback_data=AdminMenuCB(section="settings"))
    builder.adjust(1)
    return builder.as_markup()


def admin_back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=T.BTN_BACK, callback_data=AdminMenuCB(section="root"))
    return builder.as_markup()


def admin_payments_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=T.BTN_PENDING_PAYMENTS, callback_data=AdminPaymentListCB(status="pending", offset=0))
    builder.button(text=T.BTN_APPROVED_PAYMENTS, callback_data=AdminPaymentListCB(status="approved", offset=0))
    builder.button(text=T.BTN_REJECTED_PAYMENTS, callback_data=AdminPaymentListCB(status="rejected", offset=0))
    builder.button(text=T.BTN_BACK, callback_data=AdminMenuCB(section="root"))
    builder.adjust(1)
    return builder.as_markup()


def admin_payment_decision_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=T.BTN_APPROVE, callback_data=AdminPaymentActionCB(payment_id=payment_id, action="approve"))
    builder.button(text=T.BTN_REJECT, callback_data=AdminPaymentActionCB(payment_id=payment_id, action="reject"))
    builder.adjust(2)
    return builder.as_markup()


def admin_payments_list_keyboard(payments: Sequence[Payment], status: str, offset: int, has_more: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if status == "pending":
        for payment in payments:
            builder.button(text=T.BTN_APPROVE + f" #{payment.id}", callback_data=AdminPaymentActionCB(payment_id=payment.id, action="approve"))
            builder.button(text=T.BTN_REJECT + f" #{payment.id}", callback_data=AdminPaymentActionCB(payment_id=payment.id, action="reject"))
        builder.adjust(2)
    if offset > 0:
        builder.button(text="⬅️", callback_data=AdminPaymentListCB(status=status, offset=max(0, offset - 10)))
    if has_more:
        builder.button(text="➡️", callback_data=AdminPaymentListCB(status=status, offset=offset + 10))
    builder.button(text=T.BTN_BACK, callback_data=AdminMenuCB(section="payments"))
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def admin_users_list_keyboard(users: Sequence[User], offset: int, has_more: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users:
        if user.is_banned:
            builder.button(text=f"{T.BTN_UNBAN_USER} {user.telegram_id}", callback_data=AdminUserActionCB(user_id=user.telegram_id, action="unban"))
        else:
            builder.button(text=f"{T.BTN_BAN_USER} {user.telegram_id}", callback_data=AdminUserActionCB(user_id=user.telegram_id, action="ban"))
    builder.adjust(1)
    if offset > 0:
        builder.button(text="⬅️", callback_data=AdminUserListCB(offset=max(0, offset - 10)))
    if has_more:
        builder.button(text="➡️", callback_data=AdminUserListCB(offset=offset + 10))
    builder.button(text=T.BTN_BACK, callback_data=AdminMenuCB(section="root"))
    builder.adjust(1)
    return builder.as_markup()


def admin_ads_list_keyboard(ads: Sequence[Advertisement], status: str, offset: int, has_more: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if status == "active":
        for ad in ads:
            builder.button(text=f"⛔ #{ad.id} to'xtatish", callback_data=AdminAdActionCB(ad_id=ad.id, action="force_stop"))
        builder.adjust(1)
    if offset > 0:
        builder.button(text="⬅️", callback_data=AdminAdListCB(status=status, offset=max(0, offset - 10)))
    if has_more:
        builder.button(text="➡️", callback_data=AdminAdListCB(status=status, offset=offset + 10))
    builder.button(text=T.BTN_BACK, callback_data=AdminMenuCB(section="root"))
    builder.adjust(1)
    return builder.as_markup()


def admin_groups_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=T.BTN_ADD_GROUP, callback_data=AdminGroupMenuCB(action="add"))
    builder.button(text=T.BTN_LIST_GROUPS, callback_data=AdminGroupMenuCB(action="list"))
    builder.button(text=T.BTN_DELETE_GROUP, callback_data=AdminGroupMenuCB(action="delete"))
    builder.button(text=T.BTN_REFRESH_GROUPS, callback_data=AdminGroupMenuCB(action="refresh"))
    builder.button(text=T.BTN_BACK, callback_data=AdminMenuCB(section="root"))
    builder.adjust(1)
    return builder.as_markup()


def admin_groups_list_keyboard(groups: Sequence[Group], offset: int, has_more: bool, deletable: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if deletable:
        for group in groups:
            title = (group.title or str(group.chat_id))[:30]
            builder.button(text=f"🗑 {title}", callback_data=AdminGroupDeleteCB(group_id=group.id, confirm="ask"))
        builder.adjust(1)
    if offset > 0:
        builder.button(text="⬅️", callback_data=AdminGroupListCB(offset=max(0, offset - 10)))
    if has_more:
        builder.button(text="➡️", callback_data=AdminGroupListCB(offset=offset + 10))
    builder.button(text=T.BTN_BACK, callback_data=AdminGroupMenuCB(action="back"))
    builder.adjust(1)
    return builder.as_markup()


def admin_group_delete_confirm_keyboard(group_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=T.BTN_YES, callback_data=AdminGroupDeleteCB(group_id=group_id, confirm="yes"))
    builder.button(text=T.BTN_NO, callback_data=AdminGroupDeleteCB(group_id=group_id, confirm="no"))
    builder.adjust(2)
    return builder.as_markup()
