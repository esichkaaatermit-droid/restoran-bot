"""Главный роутер админ-панели"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.keyboards.admin_keyboards import get_admin_menu_keyboard

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message, user=None):
    """Вход в админ-панель по команде /admin"""
    if not user or user.role.value != "manager":
        await message.answer("❌ У вас нет доступа к панели управления.")
        return

    await message.answer(
        "⚙️ <b>Панель управления</b>\n\nВыберите раздел:",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin:back")
async def admin_back(callback: CallbackQuery, user=None):
    """Вернуться в главное меню админки"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    await callback.message.edit_text(
        "⚙️ <b>Панель управления</b>\n\nВыберите раздел:",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """Заглушка для неактивных кнопок"""
    await callback.answer()
