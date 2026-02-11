"""Управление сотрудниками (админ)"""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.database import async_session_maker
from database.repositories import UserRepository
from bot.keyboards.admin_keyboards import (
    get_admin_users_keyboard,
    get_users_list_keyboard,
    get_user_detail_keyboard,
)
from bot.utils import get_role_name

router = Router()


# ========== МЕНЮ СОТРУДНИКОВ ==========

@router.callback_query(F.data == "admin:users")
async def admin_users_menu(callback: CallbackQuery, user=None):
    """Меню управления сотрудниками"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    await callback.message.edit_text(
        "👥 <b>Управление сотрудниками</b>",
        reply_markup=get_admin_users_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_users:list")
async def admin_users_list(callback: CallbackQuery, user=None):
    """Список сотрудников"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all()

    if not users:
        await callback.message.edit_text(
            "👥 Список сотрудников пуст.",
            reply_markup=get_admin_users_keyboard(),
            parse_mode="HTML",
        )
        return

    await callback.message.edit_text(
        f"👥 <b>Сотрудники</b> ({len(users)})\n\n"
        "✅ — активен, ❌ — заблокирован\n"
        "📱 — Telegram привязан, ⬜ — нет\n"
        "[Х]остес [О]фициант [Б]армен [М]енеджер",
        reply_markup=get_users_list_keyboard(users),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_users:page:"))
async def admin_users_page(callback: CallbackQuery, user=None):
    """Пагинация списка"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    page = int(callback.data.split(":")[-1])

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all()

    await callback.message.edit_text(
        f"👥 <b>Сотрудники</b> ({len(users)})\n\n"
        "✅ — активен, ❌ — заблокирован\n"
        "📱 — Telegram привязан, ⬜ — нет",
        reply_markup=get_users_list_keyboard(users, page=page),
        parse_mode="HTML",
    )


# ========== ДЕТАЛИ СОТРУДНИКА ==========

@router.callback_query(F.data.regexp(r"^admin_user:(\d+)$"))
async def admin_user_detail(callback: CallbackQuery, user=None):
    """Детали сотрудника"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    user_id = int(callback.data.split(":")[1])

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        target_user = await user_repo.get_by_id(user_id)

    if not target_user:
        await callback.message.edit_text("Сотрудник не найден.")
        return

    status = "✅ Активен" if target_user.is_active else "❌ Заблокирован"
    tg = f"📱 {target_user.telegram_id}" if target_user.telegram_id else "⬜ Не привязан"

    text = (
        f"👤 <b>{target_user.full_name}</b>\n\n"
        f"📞 Телефон: {target_user.phone}\n"
        f"🏷 Должность: {get_role_name(target_user.role)}\n"
        f"🏢 Филиал: {target_user.branch}\n"
        f"📊 Статус: {status}\n"
        f"💬 Telegram: {tg}\n"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_user_detail_keyboard(target_user),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_user:block:"))
async def admin_user_block(callback: CallbackQuery, user=None):
    """Заблокировать сотрудника"""
    await callback.answer("Сотрудник заблокирован")
    if not user or user.role.value != "manager":
        return

    user_id = int(callback.data.split(":")[-1])

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        await user_repo.update(user_id, is_active=False)
        target_user = await user_repo.get_by_id(user_id)

    if target_user:
        await callback.message.edit_text(
            f"🚫 Сотрудник <b>{target_user.full_name}</b> заблокирован.",
            reply_markup=get_user_detail_keyboard(target_user),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("admin_user:unblock:"))
async def admin_user_unblock(callback: CallbackQuery, user=None):
    """Разблокировать сотрудника"""
    await callback.answer("Сотрудник разблокирован")
    if not user or user.role.value != "manager":
        return

    user_id = int(callback.data.split(":")[-1])

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        await user_repo.update(user_id, is_active=True)
        target_user = await user_repo.get_by_id(user_id)

    if target_user:
        await callback.message.edit_text(
            f"✅ Сотрудник <b>{target_user.full_name}</b> разблокирован.",
            reply_markup=get_user_detail_keyboard(target_user),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("admin_user:unbind:"))
async def admin_user_unbind(callback: CallbackQuery, user=None):
    """Отвязать Telegram"""
    await callback.answer("Telegram отвязан")
    if not user or user.role.value != "manager":
        return

    user_id = int(callback.data.split(":")[-1])

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        await user_repo.update(user_id, telegram_id=None)
        target_user = await user_repo.get_by_id(user_id)

    if target_user:
        await callback.message.edit_text(
            f"🔓 Telegram отвязан от <b>{target_user.full_name}</b>.\n"
            "Сотрудник сможет заново привязать аккаунт через /start.",
            reply_markup=get_user_detail_keyboard(target_user),
            parse_mode="HTML",
        )
