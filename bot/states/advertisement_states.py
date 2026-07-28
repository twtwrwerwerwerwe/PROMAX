# -*- coding: utf-8 -*-
"""bot/states/advertisement_states.py — E'lon yaratish/tahrirlash FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class AdCreationStates(StatesGroup):
    waiting_text = State()
    waiting_interval = State()
    waiting_confirmation = State()


class AdEditStates(StatesGroup):
    choosing_field = State()
    waiting_new_text = State()
    waiting_new_interval = State()
    waiting_new_text_for_both = State()
    waiting_new_interval_for_both = State()
