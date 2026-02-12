from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards import get_menu_type_keyboard

router = Router()


async def _try_delete(message: Message):
    """Удалить сообщение пользователя, чтобы не засорять чат"""
    try:
        await message.delete()
    except Exception:
        pass


@router.message(F.text == "🍽 Меню")
async def menu_section(message: Message, user=None):
    """Раздел Меню"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return

    await _try_delete(message)
    await message.answer(
        "Выберите раздел меню:",
        reply_markup=get_menu_type_keyboard(),
    )


@router.message(F.text == "📚 Обучение")
async def training_section(message: Message, user=None):
    """Раздел Обучение"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return

    await _try_delete(message)
    from bot.routers.training import show_training_materials
    await show_training_materials(message, user)


@router.message(F.text == "📝 Аттестация")
async def test_section(message: Message, user=None):
    """Раздел Аттестация"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return

    await _try_delete(message)
    from bot.utils import are_tests_active
    tests_on = await are_tests_active(user.branch)
    if not tests_on:
        await message.answer(
            "📝 Аттестация сейчас не проводится.\n"
            "Когда менеджер назначит тестирование, кнопка появится в меню."
        )
        return

    from bot.routers.tests import show_tests
    await show_tests(message, user)


@router.message(F.text == "📋 Чек-лист")
async def checklist_section(message: Message, user=None):
    """Раздел Чек-лист"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return

    await _try_delete(message)
    from bot.routers.checklist import show_checklist
    await show_checklist(message, user)


@router.message(F.text == "🚫 Стоп-лист")
async def stop_list_section(message: Message, user=None):
    """Раздел Стоп-лист"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return

    await _try_delete(message)
    from bot.routers.lists import show_stop_list
    await show_stop_list(message, user)


@router.message(F.text == "✅ Go-лист")
async def go_list_section(message: Message, user=None):
    """Раздел Go-лист"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return

    await _try_delete(message)
    from bot.routers.lists import show_go_list
    await show_go_list(message, user)


@router.message(F.text == "💪 Мотивация")
async def motivation_section(message: Message, user=None):
    """Раздел Мотивация"""
    if not user:
        await message.answer(
            "Пожалуйста, используйте команду /start для авторизации."
        )
        return

    await _try_delete(message)
    from bot.routers.motivation import show_motivation
    await show_motivation(message, user)
