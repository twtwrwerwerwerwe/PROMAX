# -*- coding: utf-8 -*-
"""
bot/handlers/user/payment.py — To'lov tizimi (foydalanuvchi tomoni).

Eski loyihadagi `handlers/payment.py` ish jarayonining porti: tarif tanlash
-> to'lov usuli tanlash -> chek/karta/admin bilan bog'lanish -> adminlarga
bildirishnoma. UI yangi botga moslashtirilgan, ammo biznes-logika bir xil.
"""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.core.containers import ServiceContainer
from bot.keyboards.admin_inline import admin_payment_decision_keyboard
from bot.keyboards.inline import payment_methods_keyboard, tariffs_keyboard
from bot.keyboards.reply import phone_request_keyboard
from bot.keyboards.callback_data import ContinueCB, PayMethodCB, TariffCB
from bot.states.registration_states import PaymentStates, PhoneStates
from bot.utils.text_templates import T

logger = logging.getLogger("payment")

router = Router(name="user_payment")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")


@router.callback_query(ContinueCB.filter())
async def on_continue(callback: CallbackQuery, services: ServiceContainer, state: FSMContext) -> None:
    await callback.answer()
    user = await services.users.get_or_create(
        callback.from_user.id, callback.from_user.username, callback.from_user.full_name
    )

    if user.has_active_subscription:
        if user.phone_number:
            from bot.handlers.user.main_menu import show_main_menu
            await show_main_menu(callback.message, services)
            return
        await callback.message.answer(T.ASK_PHONE, reply_markup=phone_request_keyboard())
        await state.set_state(PhoneStates.waiting_phone)
        return

    tariffs = {tc.key: tc.tariff for tc in services.payments.list_tariffs()}
    await callback.message.answer(T.CHOOSE_TARIFF, reply_markup=tariffs_keyboard(tariffs))
    await state.set_state(PaymentStates.choosing_tariff)


@router.callback_query(TariffCB.filter())
async def on_tariff_chosen(callback: CallbackQuery, callback_data: TariffCB, services: ServiceContainer, state: FSMContext) -> None:
    await callback.answer()
    tariff = services.payments.get_tariff(callback_data.tariff_key)
    if tariff is None:
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        return

    await state.update_data(tariff_key=callback_data.tariff_key)
    await state.set_state(PaymentStates.choosing_method)

    price_fmt = f"{tariff.price:,}".replace(",", " ")
    await callback.message.answer(
        T.CHOOSE_PAYMENT_METHOD.format(tariff_label=tariff.label, price=price_fmt),
        reply_markup=payment_methods_keyboard(callback_data.tariff_key),
    )


@router.callback_query(PayMethodCB.filter())
async def on_payment_method_chosen(
    callback: CallbackQuery, callback_data: PayMethodCB, services: ServiceContainer, state: FSMContext, bot: Bot
) -> None:
    await callback.answer()
    tariff = services.payments.get_tariff(callback_data.tariff_key)
    if tariff is None:
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        return

    method = callback_data.method

    if method == "click" and not settings.click_merchant_id:
        await callback.message.answer(T.PAYMENT_METHOD_UNAVAILABLE)
        return
    if method == "payme" and not settings.payme_merchant_id:
        await callback.message.answer(T.PAYMENT_METHOD_UNAVAILABLE)
        return

    if method == "receipt":
        await state.update_data(tariff_key=callback_data.tariff_key, method="receipt")
        await state.set_state(PaymentStates.waiting_receipt_photo)
        card = settings.payment_card
        await callback.message.answer(
            T.RECEIPT_CARD_INFO.format(card_number=card["number"], card_owner=card["owner"])
        )
        await callback.message.answer(T.ASK_RECEIPT_PHOTO)
        return

    if method == "contact_admin":
        payment = await services.payments.create_payment_request(
            user_id=callback.from_user.id,
            tariff_key=callback_data.tariff_key,
            method="contact_admin",
        )
        await _notify_admins(bot, services, payment, callback.from_user)
        await callback.message.answer(
            T.CONTACT_ADMIN_PAYMENT.format(admin_name=settings.admin_name, admin_phone=settings.admin_phone)
        )
        await state.clear()
        return

    # click / payme configured but not yet integrated in this build — graceful fallback.
    await callback.message.answer(T.PAYMENT_METHOD_UNAVAILABLE)


@router.message(PaymentStates.waiting_receipt_photo, F.photo)
async def on_receipt_photo(message: Message, services: ServiceContainer, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    tariff_key = data.get("tariff_key")
    tariff = services.payments.get_tariff(tariff_key) if tariff_key else None
    if tariff is None:
        await message.answer(T.UNKNOWN_CALLBACK)
        await state.clear()
        return

    file_id = message.photo[-1].file_id
    payment = await services.payments.create_payment_request(
        user_id=message.from_user.id,
        tariff_key=tariff_key,
        method="receipt",
        receipt_file_id=file_id,
    )
    await _notify_admins(bot, services, payment, message.from_user, photo_file_id=file_id)
    await message.answer(T.RECEIPT_RECEIVED)
    await state.clear()


@router.message(PaymentStates.waiting_receipt_photo)
async def on_receipt_invalid(message: Message) -> None:
    await message.answer(T.RECEIPT_INVALID)


async def _notify_admins(bot: Bot, services: ServiceContainer, payment, from_user, photo_file_id: str | None = None) -> None:
    method_labels = {
        "receipt": T.PAY_METHOD_RECEIPT,
        "click": T.PAY_METHOD_CLICK,
        "payme": T.PAY_METHOD_PAYME,
        "contact_admin": T.PAY_METHOD_CONTACT_ADMIN,
    }
    user_display = from_user.full_name or (f"@{from_user.username}" if from_user.username else str(from_user.id))
    text = T.PAYMENT_PENDING_ADMIN_NOTIFY.format(
        user_display=user_display,
        user_id=from_user.id,
        tariff_label=payment.tariff_label,
        price=f"{payment.price:,}".replace(",", " "),
        method_label=method_labels.get(payment.method, payment.method),
    )
    keyboard = admin_payment_decision_keyboard(payment.id)

    for admin_id in settings.admin_ids:
        try:
            if photo_file_id:
                sent = await bot.send_photo(admin_id, photo_file_id, caption=text, reply_markup=keyboard)
            else:
                sent = await bot.send_message(admin_id, text, reply_markup=keyboard)
            await services.payments.register_admin_notification(payment.id, admin_id, sent.message_id)
        except TelegramAPIError:
            logger.warning("Admin %s ga to'lov bildirishnomasi yuborilmadi.", admin_id)
