"""Общие утилиты для бота"""

from database.models import UserRole

ROLE_NAMES = {
    UserRole.HOSTESS: "Хостес",
    UserRole.WAITER: "Официант",
    UserRole.BARTENDER: "Бармен",
    UserRole.MANAGER: "Менеджер",
}


def get_role_name(role: UserRole) -> str:
    """Получить читаемое название роли"""
    return ROLE_NAMES.get(role, str(role.value))
