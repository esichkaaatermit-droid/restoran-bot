"""Управление аттестацией (админ)"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import update

from database.database import async_session_maker
from database.repositories import TestRepository
from database.models import Test
from bot.keyboards.admin_keyboards import get_attest_keyboard

router = Router()


@router.callback_query(F.data == "admin:attest")
async def admin_attest(callback: CallbackQuery, user=None):
    """Меню управления аттестацией"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    async with async_session_maker() as session:
        test_repo = TestRepository(session)
        tests = await test_repo.get_all_tests(user.branch)

    active = any(t.is_active for t in tests)

    await callback.message.edit_text(
        f"📝 <b>Управление аттестацией</b>\n\n"
        f"Всего тестов: {len(tests)}\n"
        f"Статус: {'🟢 Включена' if active else '🔴 Выключена'}",
        reply_markup=get_attest_keyboard(active),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_attest:on")
async def admin_attest_on(callback: CallbackQuery, user=None):
    """Включить аттестацию"""
    await callback.answer("Аттестация включена")
    if not user or user.role.value != "manager":
        return

    async with async_session_maker() as session:
        await session.execute(
            update(Test).where(Test.branch == user.branch).values(is_active=True)
        )
        await session.commit()

    await callback.message.edit_text(
        "📝 <b>Аттестация</b>\n\n🟢 Все тесты <b>включены</b>.",
        reply_markup=get_attest_keyboard(True),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_attest:off")
async def admin_attest_off(callback: CallbackQuery, user=None):
    """Выключить аттестацию"""
    await callback.answer("Аттестация выключена")
    if not user or user.role.value != "manager":
        return

    async with async_session_maker() as session:
        await session.execute(
            update(Test).where(Test.branch == user.branch).values(is_active=False)
        )
        await session.commit()

    await callback.message.edit_text(
        "📝 <b>Аттестация</b>\n\n🔴 Все тесты <b>выключены</b>.",
        reply_markup=get_attest_keyboard(False),
        parse_mode="HTML",
    )
