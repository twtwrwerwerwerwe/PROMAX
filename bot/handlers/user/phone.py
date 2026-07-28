# -*- coding: utf-8 -*-
"""bot/handlers/user/phone.py — Telefon raqamini qabul qilish (kontakt yoki qo'lda)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.core.containers import ServiceContainer
from bot.exceptions import InvalidPhoneNumberError
from bot.keyboards.reply import main_menu_keyboard
from bot.config import settings
import re
from bot.states.registration_states import PhoneStates
from bot.utils.phone import format_phone_pretty
from bot.utils.text_templates import T

router = Router(name="user_phone")
router.message.filter(F.chat.type == "private")


@router.message(PhoneStates.waiting_phone, F.contact)
async def on_contact_phone(message: Message, services: ServiceContainer, state: FSMContext) -> None:
    raw = message.contact.phone_number
    await _save_and_continue(message, services, state, raw)


@router.message(PhoneStates.waiting_phone, F.text)
async def on_text_phone(message: Message, services: ServiceContainer, state: FSMContext) -> None:
    await _save_and_continue(message, services, state, message.text)


# Fallback handlers: allow users who have just received admin approval to
# send their contact/text even if no FSM state was set. This covers the case
# where the admin approves the payment and the bot prompts the user to share
# their phone, but the user's FSM wasn't initialized (e.g. they didn't press
# a Continue button).
@router.message(F.contact)
async def on_contact_phone_no_state(message: Message, services: ServiceContainer, state: FSMContext) -> None:
    # If user already has phone, ignore.
    if await services.users.has_phone(message.from_user.id):
        return

    user = await services.users.get(message.from_user.id)
    if user is None or not user.has_active_subscription:
        return

    raw = message.contact.phone_number
    await _save_and_continue(message, services, state, raw)


@router.message(F.text)
async def on_text_phone_no_state(message: Message, services: ServiceContainer, state: FSMContext) -> None:
    # Accept manual phone text after approval even without explicit FSM state.
    if await services.users.has_phone(message.from_user.id):
        return

    user = await services.users.get(message.from_user.id)
    if user is None or not user.has_active_subscription:
        return

    # Basic heuristic: treat the text as a phone number only if it contains
    # at least 6 digits. This avoids intercepting menu button presses.
    digits = re.sub(r"\D", "", message.text or "")
    if len(digits) < 6:
        return

    await _save_and_continue(message, services, state, message.text)


async def _save_and_continue(message: Message, services: ServiceContainer, state: FSMContext, raw_phone: str) -> None:
    try:
        normalized = await services.users.save_phone(message.from_user.id, raw_phone)
    except InvalidPhoneNumberError:
        await message.answer(T.PHONE_INVALID)
        return

    await state.clear()
    await message.answer(T.PHONE_SAVED.format(phone=format_phone_pretty(normalized)))
    await message.answer(T.MAIN_MENU_TEXT, reply_markup=main_menu_keyboard(is_admin=(message.from_user.id in settings.admin_ids)))
