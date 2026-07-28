# -*- coding: utf-8 -*-
"""
bot/handlers/admin/payments.py — Admin panel: To'lovlar bo'limi.

Eski loyihadagi `handlers/payment_admin.py` mantig'ining porti: tasdiqlash/
rad etish, ikki marta qayta ishlashdan himoya, va barcha adminlarga
yuborilgan bildirishnomalarni qarordan so'ng tahrirlash (edit).
"""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.core.containers import ServiceContainer
from bot.exceptions import PaymentAlreadyProcessedError
from bot.filters import IsAdmin
from bot.keyboards.admin_inline import admin_payments_list_keyboard, admin_payments_menu_keyboard
from bot.keyboards.callback_data import AdminMenuCB, AdminPaymentActionCB, AdminPaymentListCB

from bot.states.registration_states import RejectPaymentStates
from bot.utils.formatting import format_datetime
from bot.utils.text_templates import T
from bot.keyboards.reply import phone_request_keyboard

logger = logging.getLogger("admin")

router = Router(name="admin_payments")
router.message.filter(F.chat.type == "private", IsAdmin())
router.callback_query.filter(F.message.chat.type == "private", IsAdmin())

PAGE_SIZE = 10


@router.callback_query(AdminMenuCB.filter(F.section == "payments"))
async def on_payments_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(T.ADMIN_PAYMENTS_MENU_TITLE, reply_markup=admin_payments_menu_keyboard())


@router.callback_query(AdminPaymentListCB.filter())
async def on_payments_list(callback: CallbackQuery, callback_data: AdminPaymentListCB, services: ServiceContainer) -> None:
    await callback.answer()
    payments = await services.payments.list_by_status(callback_data.status, callback_data.offset, PAGE_SIZE + 1)
    has_more = len(payments) > PAGE_SIZE
    payments = payments[:PAGE_SIZE]

    if not payments:
        await callback.message.answer(T.PAYMENTS_LIST_EMPTY, reply_markup=admin_payments_menu_keyboard())
        return

    lines = []
    for p in payments:
        lines.append(
            f"#{p.id} | user={p.user_id} | {p.tariff_label} | {p.price:,} so'm | {format_datetime(p.created_at)}".replace(",", " ")
        )
    text = "\n".join(lines)

    await callback.message.answer(
        text,
        reply_markup=admin_payments_list_keyboard(payments, callback_data.status, callback_data.offset, has_more),
    )


@router.callback_query(AdminPaymentActionCB.filter(F.action == "approve"))
async def on_approve(callback: CallbackQuery, callback_data: AdminPaymentActionCB, services: ServiceContainer, bot: Bot) -> None:
    await callback.answer()
    try:
        payment = await services.payments.approve_payment(callback_data.payment_id, callback.from_user.id)
    except PaymentAlreadyProcessedError:
        await callback.answer(T.PAYMENT_ALREADY_PROCESSED, show_alert=True)
        return

    await _update_admin_notifications(bot, payment, approved=True, admin_name=callback.from_user.full_name)
    await _notify_user_decision(bot, services, payment, approved=True)
    logger.info("To'lov #%s tasdiqlandi (admin=%s)", payment.id, callback.from_user.id)


@router.callback_query(AdminPaymentActionCB.filter(F.action == "reject"))
async def on_reject_start(callback: CallbackQuery, callback_data: AdminPaymentActionCB, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(reject_payment_id=callback_data.payment_id)
    await state.set_state(RejectPaymentStates.waiting_reason)
    await callback.message.answer(T.ASK_REJECT_REASON)


@router.message(RejectPaymentStates.waiting_reason, F.text)
async def on_reject_reason(message: Message, services: ServiceContainer, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    payment_id = data.get("reject_payment_id")
    reason = message.text.strip()
    await state.clear()

    try:
        payment = await services.payments.reject_payment(payment_id, message.from_user.id, reason)
    except PaymentAlreadyProcessedError:
        await message.answer(T.PAYMENT_ALREADY_PROCESSED)
        return

    await _update_admin_notifications(bot, payment, approved=False, admin_name=message.from_user.full_name, reason=reason)
    await _notify_user_decision(bot, services, payment, approved=False, reason=reason)
    logger.info("To'lov #%s rad etildi (admin=%s) sabab=%s", payment.id, message.from_user.id, reason)


async def _update_admin_notifications(bot: Bot, payment, approved: bool, admin_name: str, reason: str = "") -> None:
    notice = (
        T.PAYMENT_DECIDED_NOTICE_APPROVED.format(admin_name=admin_name)
        if approved
        else T.PAYMENT_DECIDED_NOTICE_REJECTED.format(admin_name=admin_name, reason=reason)
    )
    for entry in payment.admin_notifications or []:
        try:
            if payment.receipt_file_id:
                await bot.edit_message_caption(
                    chat_id=entry["admin_id"], message_id=entry["message_id"], caption=notice
                )
            else:
                await bot.edit_message_text(
                    chat_id=entry["admin_id"], message_id=entry["message_id"], text=notice
                )
        except TelegramAPIError:
            logger.warning("Admin bildirishnomasini tahrirlab bo'lmadi: %s", entry)


async def _notify_user_decision(bot: Bot, services: ServiceContainer, payment, approved: bool, reason: str = "") -> None:
    if approved:
        if payment.days is None:
            expiry_line = T.PAYMENT_APPROVED_LIFETIME_LINE
        else:
            import datetime as dt
            end_date = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=payment.days)).strftime("%Y-%m-%d")
            expiry_line = T.PAYMENT_APPROVED_EXPIRY_LINE.format(end_date=end_date)
        text = T.PAYMENT_APPROVED_USER.format(tariff_label=payment.tariff_label, expiry_line=expiry_line)
    else:
        text = T.PAYMENT_REJECTED_USER.format(
            reason=reason or "—", admin_name=settings.admin_name, admin_phone=settings.admin_phone
        )
    try:
        await bot.send_message(payment.user_id, text)
    except TelegramAPIError:
        logger.warning("Foydalanuvchi %s ga to'lov qarori haqida xabar yuborilmadi.", payment.user_id)

    # If payment approved but user doesn't yet have a phone number, prompt them
    # to share their contact. Some users may not have an FSM state set, so we
    # additionally provide a permissive reply-keyboard prompt; handlers accept
    # contact/text even without an explicit FSM state (see user/phone.py).
    if approved:
        try:
            has_phone = await services.users.has_phone(payment.user_id)
            if not has_phone:
                await bot.send_message(payment.user_id, T.ASK_PHONE, reply_markup=phone_request_keyboard())
        except TelegramAPIError:
            logger.warning("Foydalanuvchi %s ga telefon so'rovi yuborilmadi.", payment.user_id)
