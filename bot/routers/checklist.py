"""Чек-листы для сотрудников"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.database import async_session_maker
from database.repositories import ChecklistRepository
from bot.keyboards import (
    get_checklist_categories_keyboard,
    get_checklist_back_keyboard,
)

router = Router()


async def show_checklist(message: Message, user):
    """Показать чек-лист для роли сотрудника"""
    async with async_session_maker() as session:
        checklist_repo = ChecklistRepository(session)
        categories = await checklist_repo.get_categories_by_role(user.role, user.branch)

    if not categories:
        # Если категорий нет — попробуем показать все задачи без категорий
        async with async_session_maker() as session:
            checklist_repo = ChecklistRepository(session)
            items = await checklist_repo.get_by_role(user.role, user.branch)

        if not items:
            await message.answer(
                "📋 Для Вашей должности пока нет чек-листа.\n"
                "Обратитесь к менеджеру."
            )
            return

        # Показываем все задачи одним списком
        text = "📋 <b>Ваш чек-лист</b>\n\n"
        for i, item in enumerate(items, 1):
            text += f"{i}. {item.task}\n"

        await message.answer(text, parse_mode="HTML")
        return

    await message.answer(
        "📋 <b>Чек-лист</b>\n\n"
        "Выберите категорию:",
        reply_markup=get_checklist_categories_keyboard(categories),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("checklist_cat:"))
async def show_checklist_category(callback: CallbackQuery, user=None):
    """Показать задачи чек-листа по категории"""
    await callback.answer()

    if not user:
        await callback.message.answer("Пожалуйста, используйте /start для авторизации.")
        return

    category = callback.data.split(":", 1)[1]

    async with async_session_maker() as session:
        checklist_repo = ChecklistRepository(session)
        items = await checklist_repo.get_by_category(user.role, category, user.branch)

    if not items:
        await callback.message.edit_text(
            f"📋 <b>{category}</b>\n\nВ этой категории пока нет задач.",
            reply_markup=get_checklist_back_keyboard(),
            parse_mode="HTML",
        )
        return

    text = f"📋 <b>{category}</b>\n\n"
    for i, item in enumerate(items, 1):
        text += f"  {i}. {item.task}\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_checklist_back_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "checklist:all")
async def show_full_checklist(callback: CallbackQuery, user=None):
    """Показать полный чек-лист"""
    await callback.answer()

    if not user:
        await callback.message.answer("Пожалуйста, используйте /start для авторизации.")
        return

    async with async_session_maker() as session:
        checklist_repo = ChecklistRepository(session)
        items = await checklist_repo.get_by_role(user.role, user.branch)

    if not items:
        await callback.message.edit_text(
            "📋 Чек-лист пуст.",
            reply_markup=get_checklist_back_keyboard(),
            parse_mode="HTML",
        )
        return

    text = "📋 <b>Полный чек-лист</b>\n\n"
    current_category = None

    for item in items:
        if item.category and item.category != current_category:
            current_category = item.category
            text += f"\n<b>▸ {current_category}</b>\n"
        text += f"  • {item.task}\n"

    # Telegram ограничивает сообщения 4096 символами
    if len(text) > 4000:
        text = text[:3990] + "\n\n<i>...список обрезан</i>"

    await callback.message.edit_text(
        text,
        reply_markup=get_checklist_back_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "checklist:back")
async def back_to_checklist_categories(callback: CallbackQuery, user=None):
    """Вернуться к категориям чек-листа"""
    await callback.answer()

    if not user:
        return

    async with async_session_maker() as session:
        checklist_repo = ChecklistRepository(session)
        categories = await checklist_repo.get_categories_by_role(user.role, user.branch)

    await callback.message.edit_text(
        "📋 <b>Чек-лист</b>\n\n"
        "Выберите категорию:",
        reply_markup=get_checklist_categories_keyboard(categories),
        parse_mode="HTML",
    )
