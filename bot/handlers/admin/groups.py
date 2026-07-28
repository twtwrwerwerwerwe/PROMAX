# -*- coding: utf-8 -*-
"""bot/handlers/admin/groups.py — Admin panel: Guruhlarni boshqarish (yangi funksiya)."""
from __future__ import annotations

import logging
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.core.containers import ServiceContainer
from bot.exceptions import GroupValidationError
from bot.filters import IsAdmin
from bot.keyboards.admin_inline import (
    admin_group_delete_confirm_keyboard,
    admin_groups_list_keyboard,
    admin_groups_menu_keyboard,
)
from bot.keyboards.callback_data import (
    AdminGroupDeleteCB,
    AdminGroupListCB,
    AdminGroupMenuCB,
    AdminMenuCB,
)
from bot.states.admin_states import AdminGroupStates
from bot.utils.text_templates import T

logger = logging.getLogger("admin")

router = Router(name="admin_groups")
router.message.filter(F.chat.type == "private", IsAdmin())
router.callback_query.filter(F.message.chat.type == "private", IsAdmin())

PAGE_SIZE = 10
_GROUP_ID_PATTERN = re.compile(r"^-?\d+$")

_ERROR_MESSAGES = {
    "not_admin": T.GROUP_NOT_ADMIN,
    "not_found": T.GROUP_NOT_FOUND,
    "not_a_group": T.GROUP_NOT_A_GROUP,
    "already_exists": T.GROUP_ALREADY_EXISTS,
}


@router.callback_query(AdminMenuCB.filter(F.section == "groups"))
async def on_groups_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(T.ADMIN_GROUPS_MENU_TITLE, reply_markup=admin_groups_menu_keyboard())


@router.callback_query(AdminGroupMenuCB.filter(F.action == "back"))
async def on_groups_back(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(T.ADMIN_GROUPS_MENU_TITLE, reply_markup=admin_groups_menu_keyboard())


@router.callback_query(AdminGroupMenuCB.filter(F.action == "add"))
async def on_group_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(AdminGroupStates.waiting_group_id)
    await callback.message.answer(T.ASK_GROUP_ID)


@router.message(AdminGroupStates.waiting_group_id, F.text)
async def on_group_id_received(message: Message, services: ServiceContainer, state: FSMContext) -> None:
    raw = message.text.strip()
    if not _GROUP_ID_PATTERN.match(raw):
        await message.answer(T.GROUP_INVALID_ID)
        return

    chat_id = int(raw)
    try:
        group = await services.groups.add_group(chat_id, added_by=message.from_user.id)
    except GroupValidationError as exc:
        logger.warning("Guruh qo'shishda xatolik (%s): %s", exc.code, exc)
        await message.answer(_ERROR_MESSAGES.get(exc.code, str(exc)))
        return

    await state.clear()
    logger.info("Guruh qo'shildi: chat_id=%s title=%s admin=%s", group.chat_id, group.title, message.from_user.id)
    await message.answer(T.GROUP_ADDED_OK)
    await message.answer(T.ADMIN_GROUPS_MENU_TITLE, reply_markup=admin_groups_menu_keyboard())


@router.callback_query(AdminGroupMenuCB.filter(F.action == "list"))
async def on_group_list(callback: CallbackQuery, services: ServiceContainer, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(group_mode="view")
    await _render_groups(callback, services, offset=0, deletable=False)


@router.callback_query(AdminGroupMenuCB.filter(F.action == "delete"))
async def on_group_delete_menu(callback: CallbackQuery, services: ServiceContainer, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(group_mode="delete")
    await _render_groups(callback, services, offset=0, deletable=True)


@router.callback_query(AdminGroupMenuCB.filter(F.action == "refresh"))
async def on_group_refresh(callback: CallbackQuery, services: ServiceContainer) -> None:
    await callback.answer("🔄 Tekshirilmoqda...")
    await services.groups.revalidate_all()
    await callback.message.answer(T.ADMIN_GROUPS_MENU_TITLE, reply_markup=admin_groups_menu_keyboard())


@router.callback_query(AdminGroupListCB.filter())
async def on_group_list_paginate(callback: CallbackQuery, callback_data: AdminGroupListCB, services: ServiceContainer, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    deletable = data.get("group_mode") == "delete"
    await _render_groups(callback, services, offset=callback_data.offset, deletable=deletable)


async def _render_groups(callback: CallbackQuery, services: ServiceContainer, offset: int, deletable: bool) -> None:
    groups = await services.groups.list_all(offset, PAGE_SIZE + 1)
    has_more = len(groups) > PAGE_SIZE
    groups = groups[:PAGE_SIZE]

    if not groups:
        await callback.message.answer(T.GROUPS_LIST_EMPTY, reply_markup=admin_groups_menu_keyboard())
        return

    total = await services.groups.count_all()
    active = await services.groups.count_active()
    lines = [f"🏘 Jami: {total} ta | 🟢 Aktiv: {active} ta\n"]
    for group in groups:
        status = "🟢 Aktiv" if group.is_active else "🔴 Nofaol"
        lines.append(f"{status} | {group.title or '—'} | <code>{group.chat_id}</code>")
    text = "\n".join(lines)

    await callback.message.answer(text, reply_markup=admin_groups_list_keyboard(groups, offset, has_more, deletable=deletable))


@router.callback_query(AdminGroupDeleteCB.filter(F.confirm == "ask"))
async def on_group_delete_ask(callback: CallbackQuery, callback_data: AdminGroupDeleteCB, services: ServiceContainer) -> None:
    await callback.answer()
    group = await services.groups.get(callback_data.group_id)
    if group is None:
        await callback.message.answer(T.UNKNOWN_CALLBACK)
        return
    await callback.message.answer(
        T.GROUP_DELETE_CONFIRM.format(title=group.title or str(group.chat_id)),
        reply_markup=admin_group_delete_confirm_keyboard(group.id),
    )


@router.callback_query(AdminGroupDeleteCB.filter(F.confirm == "yes"))
async def on_group_delete_confirm(callback: CallbackQuery, callback_data: AdminGroupDeleteCB, services: ServiceContainer) -> None:
    await callback.answer()
    await services.groups.delete_group(callback_data.group_id)
    logger.info("Guruh o'chirildi: group_id=%s admin=%s", callback_data.group_id, callback.from_user.id)
    await callback.message.answer(T.GROUP_DELETED)
    await callback.message.answer(T.ADMIN_GROUPS_MENU_TITLE, reply_markup=admin_groups_menu_keyboard())


@router.callback_query(AdminGroupDeleteCB.filter(F.confirm == "no"))
async def on_group_delete_cancel(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(T.ADMIN_GROUPS_MENU_TITLE, reply_markup=admin_groups_menu_keyboard())
