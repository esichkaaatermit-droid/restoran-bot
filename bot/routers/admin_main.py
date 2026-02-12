"""Главный роутер админ-панели"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command

from bot.keyboards.admin_keyboards import get_admin_menu_keyboard, get_main_menu_keyboard
from bot.keyboards import get_menu_type_keyboard
from bot.utils import are_tests_active

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message, user=None):
    """Вход в админ-панель по команде /admin"""
    if not user or user.role.value != "manager":
        await message.answer("❌ У вас нет доступа к панели управления.")
        return

    try:
        await message.delete()
    except Exception:
        pass

    # Скрываем Reply-клавиатуру, чтобы не было двух меню
    hide_msg = await message.answer("⚙️", reply_markup=ReplyKeyboardRemove())
    try:
        await hide_msg.delete()
    except Exception:
        pass

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


@router.callback_query(F.data == "admin:exit")
async def admin_exit(callback: CallbackQuery, user=None):
    """Выход из админки — удаляем inline-панель, возвращаем Reply-клавиатуру"""
    await callback.answer()

    try:
        await callback.message.delete()
    except Exception:
        pass

    if user:
        tests_on = await are_tests_active(user.branch)
        await callback.message.answer(
            "👋 Вы вышли из панели управления.",
            reply_markup=get_main_menu_keyboard(tests_on),
        )
    else:
        await callback.message.answer("Используйте /start для начала работы.")


@router.callback_query(F.data == "admin:menu")
async def admin_menu_section(callback: CallbackQuery, user=None):
    """Открыть меню блюд из админки"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🍳 Меню кухни", callback_data="menu_type:kitchen"),
            InlineKeyboardButton(text="🍹 Меню бара", callback_data="menu_type:bar"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")],
    ])

    await callback.message.edit_text(
        "🍽 <b>Меню</b>\n\nВыберите раздел меню:",
        reply_markup=kb,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """Заглушка для неактивных кнопок"""
    await callback.answer()
