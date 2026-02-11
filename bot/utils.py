"""Общие утилиты для бота"""

import logging

from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from database.models import UserRole

logger = logging.getLogger(__name__)

ROLE_NAMES = {
    UserRole.HOSTESS: "Хостес",
    UserRole.WAITER: "Официант",
    UserRole.BARTENDER: "Бармен",
    UserRole.MANAGER: "Менеджер",
}


def get_role_name(role: UserRole) -> str:
    """Получить читаемое название роли"""
    return ROLE_NAMES.get(role, str(role.value))


async def safe_edit_or_send(callback: CallbackQuery, text: str, reply_markup=None, parse_mode="HTML"):
    """Безопасная навигация: edit_text, а если не получается (фото) — delete + answer"""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


async def are_tests_active(branch: str) -> bool:
    """Проверить, есть ли активные тесты для филиала"""
    from database.database import async_session_maker
    from database.repositories import TestRepository

    async with async_session_maker() as session:
        test_repo = TestRepository(session)
        tests = await test_repo.get_all_tests(branch)
    return any(t.is_active for t in tests)
