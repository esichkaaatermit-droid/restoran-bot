from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards import (
    get_main_menu_keyboard,
    get_menu_type_keyboard,
)

router = Router()


@router.message(F.text == "🍽 Меню")
async def menu_section(message: Message, user=None):
    """Раздел Меню"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return
    
    await message.answer(
        "Выберите раздел меню:",
        reply_markup=get_menu_type_keyboard()
    )


@router.message(F.text == "📚 Обучение")
async def training_section(message: Message, user=None):
    """Раздел Обучение - обработка в training.py"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return
    
    # Импортируем здесь чтобы избежать циклического импорта
    from bot.routers.training import show_training_materials
    await show_training_materials(message, user)


@router.message(F.text == "📝 Аттестация")
async def test_section(message: Message, user=None):
    """Раздел Аттестация - обработка в tests.py"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return
    
    from bot.routers.tests import show_tests
    await show_tests(message, user)


@router.message(F.text == "🚫 Стоп-лист")
async def stop_list_section(message: Message, user=None):
    """Раздел Стоп-лист - обработка в lists.py"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return
    
    from bot.routers.lists import show_stop_list
    await show_stop_list(message, user)


@router.message(F.text == "✅ Go-лист")
async def go_list_section(message: Message, user=None):
    """Раздел Go-лист - обработка в lists.py"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return
    
    from bot.routers.lists import show_go_list
    await show_go_list(message, user)


@router.message(F.text == "💪 Мотивация")
async def motivation_section(message: Message, user=None):
    """Раздел Мотивация - обработка в motivation.py"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return
    
    from bot.routers.motivation import show_motivation
    await show_motivation(message, user)
