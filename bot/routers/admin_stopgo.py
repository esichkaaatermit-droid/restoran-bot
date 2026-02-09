"""Управление стоп/go-листами (админ)"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import async_session_maker
from database.repositories import UserRepository, MenuRepository
from database.models import MenuItemStatus
from bot.keyboards.admin_keyboards import (
    get_stopgo_action_keyboard,
    get_search_results_keyboard,
)

router = Router()


class StopGoSearchStates(StatesGroup):
    search_add = State()
    search_remove = State()


# ========== СТОП-ЛИСТ ==========

@router.callback_query(F.data == "admin:stop_list")
async def admin_stop_list(callback: CallbackQuery, user=None):
    """Управление стоп-листом"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    await callback.message.edit_text(
        "🚫 <b>Управление стоп-листом</b>",
        reply_markup=get_stopgo_action_keyboard("stop"),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin:go_list")
async def admin_go_list(callback: CallbackQuery, user=None):
    """Управление go-листом"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    await callback.message.edit_text(
        "✅ <b>Управление go-листом</b>",
        reply_markup=get_stopgo_action_keyboard("go"),
        parse_mode="HTML",
    )


# ========== ПРОСМОТР ==========

@router.callback_query(F.data.startswith("admin_list:view:"))
async def admin_list_view(callback: CallbackQuery, user=None):
    """Просмотр текущего стоп/go-листа"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    list_type = callback.data.split(":")[-1]

    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        if list_type == "stop":
            items = await menu_repo.get_stop_list(user.branch)
            emoji = "🚫"
            title = "Стоп-лист"
        else:
            items = await menu_repo.get_go_list(user.branch)
            emoji = "✅"
            title = "Go-лист"

    if not items:
        text = f"{emoji} <b>{title} пуст</b>"
    else:
        text = f"{emoji} <b>{title}</b> ({len(items)} позиций):\n\n"
        for item in items:
            text += f"• {item.name} — {item.price:.0f}₽\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_stopgo_action_keyboard(list_type),
        parse_mode="HTML",
    )


# ========== ДОБАВЛЕНИЕ ==========

@router.callback_query(F.data.startswith("admin_list:add:"))
async def admin_list_add_start(callback: CallbackQuery, state: FSMContext, user=None):
    """Начать поиск для добавления в стоп/go"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    list_type = callback.data.split(":")[-1]
    await state.update_data(list_type=list_type)
    await state.set_state(StopGoSearchStates.search_add)

    label = "стоп-лист" if list_type == "stop" else "go-лист"
    await callback.message.edit_text(
        f"🔍 Введите название блюда для добавления в {label}:",
        parse_mode="HTML",
    )


@router.message(StopGoSearchStates.search_add)
async def admin_list_add_search(message: Message, state: FSMContext, user=None):
    """Поиск блюда для добавления"""
    if not user or user.role.value != "manager":
        await state.clear()
        return

    data = await state.get_data()
    list_type = data.get("list_type", "stop")
    await state.clear()

    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        items = await menu_repo.search_by_name(message.text.strip(), user.branch)

    if not items:
        await message.answer(
            "❌ Ничего не найдено. Попробуйте другой запрос.",
            reply_markup=get_stopgo_action_keyboard(list_type),
        )
        return

    await message.answer(
        f"🔍 Найдено {len(items)} позиций.\n"
        "Выберите блюдо:",
        reply_markup=get_search_results_keyboard(items, "set", list_type),
    )


@router.callback_query(F.data.regexp(r"^admin_list:set:(stop|go):(\d+)$"))
async def admin_list_set_item(callback: CallbackQuery, user=None):
    """Установить статус блюда"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    parts = callback.data.split(":")
    list_type = parts[2]
    item_id = int(parts[3])

    status = MenuItemStatus.STOP if list_type == "stop" else MenuItemStatus.GO

    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        await menu_repo.update_status(item_id, status)
        item = await menu_repo.get_by_id(item_id)

    label = "стоп-лист" if list_type == "stop" else "go-лист"
    emoji = "🚫" if list_type == "stop" else "✅"

    await callback.message.edit_text(
        f"{emoji} <b>{item.name}</b> добавлено в {label}.",
        reply_markup=get_stopgo_action_keyboard(list_type),
        parse_mode="HTML",
    )


# ========== УДАЛЕНИЕ ==========

@router.callback_query(F.data.startswith("admin_list:remove:"))
async def admin_list_remove_start(callback: CallbackQuery, state: FSMContext, user=None):
    """Начать поиск для удаления из стоп/go"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    list_type = callback.data.split(":")[-1]
    await state.update_data(list_type=list_type)
    await state.set_state(StopGoSearchStates.search_remove)

    label = "стоп-листа" if list_type == "stop" else "go-листа"
    await callback.message.edit_text(
        f"🔍 Введите название блюда для удаления из {label}:",
        parse_mode="HTML",
    )


@router.message(StopGoSearchStates.search_remove)
async def admin_list_remove_search(message: Message, state: FSMContext, user=None):
    """Поиск блюда для удаления"""
    if not user or user.role.value != "manager":
        await state.clear()
        return

    data = await state.get_data()
    list_type = data.get("list_type", "stop")
    await state.clear()

    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        items = await menu_repo.search_by_name(message.text.strip(), user.branch)

    if not items:
        await message.answer(
            "❌ Ничего не найдено.",
            reply_markup=get_stopgo_action_keyboard(list_type),
        )
        return

    await message.answer(
        f"🔍 Найдено {len(items)} позиций.\nВыберите блюдо:",
        reply_markup=get_search_results_keyboard(items, "unset", list_type),
    )


@router.callback_query(F.data.regexp(r"^admin_list:unset:(stop|go):(\d+)$"))
async def admin_list_unset_item(callback: CallbackQuery, user=None):
    """Убрать статус блюда"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    parts = callback.data.split(":")
    list_type = parts[2]
    item_id = int(parts[3])

    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        await menu_repo.update_status(item_id, MenuItemStatus.NORMAL)
        item = await menu_repo.get_by_id(item_id)

    label = "стоп-листа" if list_type == "stop" else "go-листа"

    await callback.message.edit_text(
        f"✅ <b>{item.name}</b> убрано из {label}.",
        reply_markup=get_stopgo_action_keyboard(list_type),
        parse_mode="HTML",
    )


# ========== РАССЫЛКА ==========

@router.callback_query(F.data.startswith("admin_list:broadcast:"))
async def admin_list_broadcast(callback: CallbackQuery, user=None):
    """Рассылка стоп/go-листа сотрудникам"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    list_type = callback.data.split(":")[-1]

    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        user_repo = UserRepository(session)

        if list_type == "stop":
            items = await menu_repo.get_stop_list(user.branch)
            emoji = "🚫"
            title = "СТОП-ЛИСТ"
        else:
            items = await menu_repo.get_go_list(user.branch)
            emoji = "✅"
            title = "GO-ЛИСТ"

        if not items:
            await callback.message.edit_text(
                f"Список пуст, нечего рассылать.",
                reply_markup=get_stopgo_action_keyboard(list_type),
            )
            return

        text = f"{emoji} <b>{title}</b> (обновлён):\n\n"
        for item in items:
            text += f"• {item.name} — {item.price:.0f}₽\n"

        tg_users = await user_repo.get_all_with_telegram()

    sent = 0
    for tg_user in tg_users:
        try:
            await callback.bot.send_message(
                tg_user.telegram_id, text, parse_mode="HTML"
            )
            sent += 1
        except Exception:
            pass

    await callback.message.edit_text(
        f"📢 {title} разослан {sent} сотрудникам.",
        reply_markup=get_stopgo_action_keyboard(list_type),
        parse_mode="HTML",
    )
