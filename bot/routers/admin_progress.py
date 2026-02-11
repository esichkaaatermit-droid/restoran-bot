"""Прогресс обучения сотрудников (админ)"""

from typing import Optional, List
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.database import async_session_maker
from database.repositories import UserRepository, TrainingRepository, TestRepository
from database.models import User, UserRole
from bot.utils import get_role_name

router = Router()


async def calculate_user_stats(user_id: int, role: UserRole, branch: str) -> dict:
    """Подсчитать статистику пользователя"""
    async with async_session_maker() as session:
        training_repo = TrainingRepository(session)
        test_repo = TestRepository(session)
        
        # Материалы
        all_materials = await training_repo.get_materials_by_role(role, branch)
        completed_materials = 0
        for material in all_materials:
            progress = await training_repo.get_progress(user_id, material.id)
            if progress and progress.is_completed:
                completed_materials += 1
        
        material_percent = int(completed_materials / len(all_materials) * 100) if all_materials else 0
        
        # Тесты
        all_tests = await test_repo.get_tests_by_role(role, branch)
        test_results = await test_repo.get_user_results(user_id)
        
        passed_tests = {}
        for result in test_results:
            test_id = result.test_id
            if test_id not in passed_tests or result.percent > passed_tests[test_id].percent:
                passed_tests[test_id] = result
        
        passed_count = sum(1 for r in passed_tests.values() if r.passed)
        avg_test_percent = sum(r.percent for r in passed_tests.values()) / len(passed_tests) if passed_tests else 0
        
        return {
            'material_completed': completed_materials,
            'material_total': len(all_materials),
            'material_percent': material_percent,
            'test_passed': passed_count,
            'test_total': len(all_tests),
            'test_percent': int(avg_test_percent),
            'has_tests': len(test_results) > 0,
        }


async def show_progress_list(
    callback: CallbackQuery,
    user,
    role_filter: Optional[UserRole] = None,
    sort_by: str = "name"
):
    """Показать список сотрудников с фильтрами и сортировкой"""
    if not user or user.role.value != "manager":
        return
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        all_users = await user_repo.get_all()
        
        # Фильтруем активных с Telegram
        active_users = [u for u in all_users if u.is_active and u.telegram_id]
    
    if not active_users:
        await callback.message.edit_text(
            "📊 <b>Прогресс обучения</b>\n\n"
            "Нет активных сотрудников с привязанным Telegram.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]]
            ),
            parse_mode="HTML",
        )
        return
    
    # Применяем фильтр по роли
    if role_filter:
        filtered_users = [u for u in active_users if u.role == role_filter]
    else:
        filtered_users = active_users
    
    # Подсчитываем статистику для каждого пользователя
    users_with_stats = []
    for emp in filtered_users:
        stats = await calculate_user_stats(emp.id, emp.role, emp.branch)
        users_with_stats.append({
            'user': emp,
            'stats': stats
        })
    
    # Сортировка
    if sort_by == "name":
        users_with_stats.sort(key=lambda x: x['user'].full_name)
    elif sort_by == "material_percent":
        users_with_stats.sort(key=lambda x: x['stats']['material_percent'], reverse=False)  # Отстающие сверху
    elif sort_by == "test_percent":
        users_with_stats.sort(key=lambda x: x['stats']['test_percent'], reverse=False)  # Отстающие сверху
    elif sort_by == "not_tested":
        users_with_stats.sort(key=lambda x: (x['stats']['has_tests'], x['stats']['test_percent']))
    
    # Статистика по ролям
    by_role = {}
    for emp in active_users:
        if emp.role not in by_role:
            by_role[emp.role] = []
        by_role[emp.role].append(emp)
    
    # Подсчитываем среднюю статистику по ролям
    role_stats = {}
    for role, role_users in by_role.items():
        total_material = 0
        total_test = 0
        count = 0
        for emp in role_users:
            stats = await calculate_user_stats(emp.id, emp.role, emp.branch)
            total_material += stats['material_percent']
            total_test += stats['test_percent']
            count += 1
        role_stats[role] = {
            'count': count,
            'avg_material': int(total_material / count) if count else 0,
            'avg_test': int(total_test / count) if count else 0,
        }
    
    # Формируем сообщение
    text = "📊 <b>Прогресс обучения сотрудников</b>\n\n"
    
    # Статистика по ролям
    text += "<b>Сводка по должностям:</b>\n"
    for role in [UserRole.HOSTESS, UserRole.WAITER, UserRole.BARTENDER, UserRole.MANAGER]:
        if role in role_stats:
            stat = role_stats[role]
            role_name = get_role_name(role)
            text += f"  • {role_name} ({stat['count']} чел): "
            text += f"📚 {stat['avg_material']}% | 📝 {stat['avg_test']}%\n"
    
    text += f"\n<b>Показано:</b> {len(filtered_users)} из {len(active_users)} сотрудников\n"
    
    # Кнопки фильтров
    filter_buttons = []
    filter_buttons.append([
        InlineKeyboardButton(
            text="🔍 Все должности" if not role_filter else "Все должности",
            callback_data="admin_progress:filter:all"
        )
    ])
    
    filter_row = []
    for role, label in [(UserRole.HOSTESS, "Хостес"), (UserRole.WAITER, "Официанты")]:
        icon = "🔍" if role_filter == role else ""
        filter_row.append(InlineKeyboardButton(
            text=f"{icon} {label}",
            callback_data=f"admin_progress:filter:{role.value}"
        ))
    filter_buttons.append(filter_row)
    
    filter_row = []
    for role, label in [(UserRole.BARTENDER, "Бармены"), (UserRole.MANAGER, "Менеджеры")]:
        icon = "🔍" if role_filter == role else ""
        filter_row.append(InlineKeyboardButton(
            text=f"{icon} {label}",
            callback_data=f"admin_progress:filter:{role.value}"
        ))
    filter_buttons.append(filter_row)
    
    # Кнопки сортировки
    sort_buttons = []
    sort_row = []
    for sort_type, label in [("name", "По имени"), ("material_percent", "По обучению")]:
        icon = "🔽" if sort_by == sort_type else ""
        sort_row.append(InlineKeyboardButton(
            text=f"{icon} {label}",
            callback_data=f"admin_progress:sort:{sort_type}:{role_filter.value if role_filter else 'all'}"
        ))
    sort_buttons.append(sort_row)
    
    sort_row = []
    for sort_type, label in [("test_percent", "По тестам"), ("not_tested", "Не прошли")]:
        icon = "🔽" if sort_by == sort_type else ""
        sort_row.append(InlineKeyboardButton(
            text=f"{icon} {label}",
            callback_data=f"admin_progress:sort:{sort_type}:{role_filter.value if role_filter else 'all'}"
        ))
    sort_buttons.append(sort_row)
    
    # Список сотрудников
    user_buttons = []
    for item in users_with_stats[:20]:  # Ограничиваем 20 на страницу
        emp = item['user']
        stats = item['stats']
        
        # Иконки статуса
        if stats['material_percent'] < 50:
            material_icon = "🔴"
        elif stats['material_percent'] < 80:
            material_icon = "🟡"
        else:
            material_icon = "🟢"
        
        if not stats['has_tests']:
            test_icon = "⬜"
        elif stats['test_percent'] < 70:
            test_icon = "❌"
        else:
            test_icon = "✅"
        
        role_short = {
            UserRole.HOSTESS: "Х",
            UserRole.WAITER: "О",
            UserRole.BARTENDER: "Б",
            UserRole.MANAGER: "М",
        }.get(emp.role, "?")
        
        user_buttons.append([
            InlineKeyboardButton(
                text=f"{material_icon}{test_icon} [{role_short}] {emp.full_name}",
                callback_data=f"admin_progress:user:{emp.id}"
            )
        ])
    
    if len(filtered_users) > 20:
        user_buttons.append([
            InlineKeyboardButton(
                text=f"...и ещё {len(filtered_users) - 20} сотрудников",
                callback_data="noop"
            )
        ])
    
    # Собираем все кнопки
    buttons = filter_buttons + sort_buttons + user_buttons
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin:progress")
async def admin_progress(callback: CallbackQuery, user=None):
    """Показать прогресс обучения с фильтрами"""
    await callback.answer()
    await show_progress_list(callback, user, role_filter=None, sort_by="name")


@router.callback_query(F.data.startswith("admin_progress:filter:"))
async def filter_progress(callback: CallbackQuery, user=None):
    """Фильтрация по роли"""
    await callback.answer()
    filter_value = callback.data.split(":")[-1]
    
    if filter_value == "all":
        role_filter = None
    else:
        role_filter = UserRole(filter_value)
    
    await show_progress_list(callback, user, role_filter=role_filter, sort_by="name")


@router.callback_query(F.data.startswith("admin_progress:sort:"))
async def sort_progress(callback: CallbackQuery, user=None):
    """Сортировка списка"""
    await callback.answer()
    parts = callback.data.split(":")
    sort_by = parts[2]
    filter_value = parts[3]
    
    if filter_value == "all":
        role_filter = None
    else:
        role_filter = UserRole(filter_value)
    
    await show_progress_list(callback, user, role_filter=role_filter, sort_by=sort_by)


@router.callback_query(F.data.startswith("admin_progress:user:"))
async def show_user_progress(callback: CallbackQuery, user=None):
    """Показать детальный прогресс сотрудника"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return
    
    user_id = int(callback.data.split(":")[-1])
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        training_repo = TrainingRepository(session)
        test_repo = TestRepository(session)
        
        # Получаем сотрудника
        employee = await user_repo.get_by_id(user_id)
        if not employee:
            await callback.answer("Сотрудник не найден", show_alert=True)
            return
        
        # Получаем материалы для его роли
        all_materials = await training_repo.get_materials_by_role(employee.role, employee.branch)
        
        # Получаем прогресс по материалам
        completed_materials = 0
        for material in all_materials:
            progress = await training_repo.get_progress(employee.id, material.id)
            if progress and progress.is_completed:
                completed_materials += 1
        
        # Получаем тесты для его роли
        all_tests = await test_repo.get_tests_by_role(employee.role, employee.branch)
        
        # Получаем результаты тестов
        test_results = await test_repo.get_user_results(employee.id)
        
        # Подсчитываем пройденные тесты
        passed_tests = {}
        for result in test_results:
            test_id = result.test_id
            # Берем лучший результат по каждому тесту
            if test_id not in passed_tests or result.percent > passed_tests[test_id].percent:
                passed_tests[test_id] = result
        
        # Считаем успешно пройденные
        passed_count = sum(1 for r in passed_tests.values() if r.passed)
        total_tests = len(all_tests)
        
        # Средний процент по тестам
        if passed_tests:
            avg_percent = sum(r.percent for r in passed_tests.values()) / len(passed_tests)
        else:
            avg_percent = 0
    
    # Формируем сообщение
    text = f"📊 <b>Прогресс сотрудника</b>\n\n"
    text += f"👤 <b>{employee.full_name}</b>\n"
    text += f"💼 {get_role_name(employee.role)}\n"
    text += f"📍 {employee.branch}\n\n"
    
    # Обучение
    text += f"📚 <b>Обучающие материалы:</b>\n"
    if all_materials:
        percent = int(completed_materials / len(all_materials) * 100)
        progress_bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
        text += f"   {progress_bar} {completed_materials}/{len(all_materials)} ({percent}%)\n\n"
    else:
        text += "   Нет материалов\n\n"
    
    # Тесты
    text += f"📝 <b>Аттестация:</b>\n"
    if total_tests > 0:
        test_progress_bar = "█" * (passed_count * 10 // total_tests) + "░" * (10 - passed_count * 10 // total_tests)
        text += f"   {test_progress_bar} {passed_count}/{total_tests} пройдено\n"
        text += f"   Средний балл: {avg_percent:.0f}%\n\n"
    else:
        text += "   Нет тестов\n\n"
    
    # Детали по тестам
    if test_results:
        text += f"<b>Результаты тестов:</b>\n"
        # Группируем по тестам и берем последнюю попытку
        test_map = {}
        for result in test_results:
            if result.test_id not in test_map:
                test_map[result.test_id] = []
            test_map[result.test_id].append(result)
        
        for test_id, results in test_map.items():
            latest = results[0]  # Уже отсортировано по дате (desc)
            test_name = latest.test.title if latest.test else "Тест"
            
            if latest.passed:
                icon = "✅"
            else:
                icon = "❌"
            
            attempts = len(results)
            text += f"   {icon} {test_name}\n"
            text += f"      {latest.percent:.0f}% ({latest.score}/{latest.total_questions} верно)\n"
            text += f"      Попыток: {attempts}\n"
    else:
        text += "<i>Тесты ещё не проходил</i>\n"
    
    # Кнопки
    buttons = [
        [InlineKeyboardButton(text="◀️ К списку", callback_data="admin:progress")]
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )
