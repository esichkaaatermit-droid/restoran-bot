"""Статистика для админа"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.database import async_session_maker
from database.repositories import (
    UserRepository,
    MenuRepository,
    TestRepository,
    ChecklistRepository,
)
from database.models import MenuType, UserRole

router = Router()


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery, user=None):
    """Показать статистику"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    branch = user.branch

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        menu_repo = MenuRepository(session)
        test_repo = TestRepository(session)
        checklist_repo = ChecklistRepository(session)

        all_users = await user_repo.get_all()
        active_users = [u for u in all_users if u.is_active]
        tg_users = [u for u in active_users if u.telegram_id]

        kitchen_count = await menu_repo.count_by_type(MenuType.KITCHEN, branch)
        bar_count = await menu_repo.count_by_type(MenuType.BAR, branch)
        stop_items = await menu_repo.get_stop_list(branch)
        go_items = await menu_repo.get_go_list(branch)

        all_tests = await test_repo.get_all_tests(branch)
        active_tests = [t for t in all_tests if t.is_active]

        cl_waiter = await checklist_repo.count_by_role(UserRole.WAITER, branch)
        cl_manager = await checklist_repo.count_by_role(UserRole.MANAGER, branch)

    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 <b>Сотрудники:</b>\n"
        f"  Всего: {len(all_users)}\n"
        f"  Активных: {len(active_users)}\n"
        f"  С Telegram: {len(tg_users)}\n\n"
        f"🍽 <b>Меню:</b>\n"
        f"  Кухня: {kitchen_count} позиций\n"
        f"  Бар: {bar_count} позиций\n"
        f"  В стоп-листе: {len(stop_items)}\n"
        f"  В go-листе: {len(go_items)}\n\n"
        f"📋 <b>Чек-листы:</b>\n"
        f"  Официанты: {cl_waiter} задач\n"
        f"  Менеджеры: {cl_manager} задач\n\n"
        f"📝 <b>Аттестация:</b>\n"
        f"  Всего тестов: {len(all_tests)}\n"
        f"  Активных: {len(active_tests)}\n"
    )

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_kb,
        parse_mode="HTML",
    )
