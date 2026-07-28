# -*- coding: utf-8 -*-
"""bot/states/registration_states.py — To'lov va ro'yxatdan o'tish FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class PaymentStates(StatesGroup):
    choosing_tariff = State()
    choosing_method = State()
    waiting_receipt_photo = State()


class RejectPaymentStates(StatesGroup):
    waiting_reason = State()


class PhoneStates(StatesGroup):
    waiting_phone = State()
