"""Клавиатуры для админ-панели"""

from typing import List

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from database.models import MenuItem, User


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню для всех сотрудников"""
    buttons = [
        [KeyboardButton(text="🍽 Меню"), KeyboardButton(text="📚 Обучение")],
        [KeyboardButton(text="📝 Аттестация"), KeyboardButton(text="📋 Чек-лист")],
        [KeyboardButton(text="🚫 Стоп-лист"), KeyboardButton(text="✅ Go-лист")],
        [KeyboardButton(text="💪 Мотивация")],
    ]

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел",
    )


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Сотрудники", callback_data="admin:users")],
            [InlineKeyboardButton(text="🚫 Стоп-лист", callback_data="admin:stop_list")],
            [InlineKeyboardButton(text="✅ Go-лист", callback_data="admin:go_list")],
            [InlineKeyboardButton(text="📸 Фото блюд", callback_data="admin:photos")],
            [InlineKeyboardButton(text="📄 Файлы обучения", callback_data="admin:files")],
            [InlineKeyboardButton(text="📝 Аттестация вкл/выкл", callback_data="admin:attest")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin:broadcast")],
            [InlineKeyboardButton(text="🔄 Синхронизация", callback_data="admin:sync")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
        ]
    )


# ========== СОТРУДНИКИ ==========

def get_admin_users_keyboard() -> InlineKeyboardMarkup:
    """Меню управления сотрудниками"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Список сотрудников", callback_data="admin_users:list")],
            [InlineKeyboardButton(text="➕ Добавить сотрудника", callback_data="admin_users:add")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")],
        ]
    )


def get_users_list_keyboard(users: List[User], page: int = 0, per_page: int = 8) -> InlineKeyboardMarkup:
    """Список сотрудников с пагинацией"""
    start = page * per_page
    end = start + per_page
    page_users = users[start:end]
    total_pages = (len(users) + per_page - 1) // per_page

    buttons = []
    for user in page_users:
        status = "✅" if user.is_active else "❌"
        tg = "📱" if user.telegram_id else "⬜"
        role_short = {
            "hostess": "Х",
            "waiter": "О",
            "bartender": "Б",
            "manager": "М",
        }.get(user.role.value, "?")
        buttons.append([
            InlineKeyboardButton(
                text=f"{status}{tg} [{role_short}] {user.full_name}",
                callback_data=f"admin_user:{user.id}",
            )
        ])

    # Пагинация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️", callback_data=f"admin_users:page:{page - 1}")
        )
    if total_pages > 1:
        nav_buttons.append(
            InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
        )
    if end < len(users):
        nav_buttons.append(
            InlineKeyboardButton(text="▶️", callback_data=f"admin_users:page:{page + 1}")
        )
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin:users")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_user_detail_keyboard(user: User) -> InlineKeyboardMarkup:
    """Детали сотрудника"""
    buttons = []
    if user.is_active:
        buttons.append([
            InlineKeyboardButton(
                text="🚫 Заблокировать", callback_data=f"admin_user:block:{user.id}"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Разблокировать", callback_data=f"admin_user:unblock:{user.id}"
            )
        ])

    if user.telegram_id:
        buttons.append([
            InlineKeyboardButton(
                text="🔓 Отвязать Telegram", callback_data=f"admin_user:unbind:{user.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="◀️ К списку", callback_data="admin_users:list")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_role_selection_keyboard() -> InlineKeyboardMarkup:
    """Выбор должности при добавлении сотрудника"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Хостес", callback_data="admin_add_role:hostess")],
            [InlineKeyboardButton(text="Официант", callback_data="admin_add_role:waiter")],
            [InlineKeyboardButton(text="Бармен", callback_data="admin_add_role:bartender")],
            [InlineKeyboardButton(text="Менеджер", callback_data="admin_add_role:manager")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin:users")],
        ]
    )


# ========== СТОП/GO ЛИСТ ==========

def get_stopgo_action_keyboard(list_type: str) -> InlineKeyboardMarkup:
    """Меню управления стоп/go-листом"""
    if list_type == "stop":
        label = "🚫 Стоп-лист"
    else:
        label = "✅ Go-лист"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📋 Текущий {label}", callback_data=f"admin_list:view:{list_type}")],
            [InlineKeyboardButton(text="➕ Добавить позицию", callback_data=f"admin_list:add:{list_type}")],
            [InlineKeyboardButton(text="➖ Убрать позицию", callback_data=f"admin_list:remove:{list_type}")],
            [InlineKeyboardButton(text="📢 Рассылка сотрудникам", callback_data=f"admin_list:broadcast:{list_type}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")],
        ]
    )


def get_search_results_keyboard(
    items: List[MenuItem], action: str, list_type: str
) -> InlineKeyboardMarkup:
    """Результаты поиска позиций меню"""
    buttons = []
    for item in items:
        status_icon = ""
        if item.status.value == "stop":
            status_icon = "🚫 "
        elif item.status.value == "go":
            status_icon = "🔥 "

        buttons.append([
            InlineKeyboardButton(
                text=f"{status_icon}{item.name} — {item.price:.0f}₽",
                callback_data=f"admin_list:{action}:{list_type}:{item.id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"admin:{list_type}_list")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ========== ФОТО ==========

def get_photo_search_results_keyboard(items: List[MenuItem]) -> InlineKeyboardMarkup:
    """Результаты поиска для привязки фото"""
    buttons = []
    for item in items:
        has_photo = "📸" if item.photo else "⬜"
        buttons.append([
            InlineKeyboardButton(
                text=f"{has_photo} {item.name}",
                callback_data=f"admin_photo:select:{item.id}",
            )
        ])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin:photos")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ========== АТТЕСТАЦИЯ ==========

def get_attest_keyboard(tests_active: bool) -> InlineKeyboardMarkup:
    """Управление аттестацией"""
    if tests_active:
        toggle_text = "🔴 Выключить аттестацию"
        toggle_data = "admin_attest:off"
    else:
        toggle_text = "🟢 Включить аттестацию"
        toggle_data = "admin_attest:on"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data=toggle_data)],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")],
        ]
    )


# ========== СИНХРОНИЗАЦИЯ ==========

def get_sync_keyboard() -> InlineKeyboardMarkup:
    """Меню синхронизации"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Синхронизировать всё", callback_data="admin_sync:all")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")],
        ]
    )
