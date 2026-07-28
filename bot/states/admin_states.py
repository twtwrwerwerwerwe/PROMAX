# -*- coding: utf-8 -*-
"""bot/states/admin_states.py — Admin panel FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class AdminGroupStates(StatesGroup):
    waiting_group_id = State()


class AdminSettingsStates(StatesGroup):
    waiting_concurrency_value = State()
    waiting_group_check_hours = State()
    waiting_auto_stop_hours = State()
