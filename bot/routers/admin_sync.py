"""Синхронизация данных из Google Sheets"""

import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards.admin_keyboards import get_sync_keyboard
from integrations.google_sheets import GoogleSheetsSync

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "admin:sync")
async def sync_menu(callback: CallbackQuery, user=None):
    """Меню синхронизации"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    await callback.message.edit_text(
        "🔄 <b>Синхронизация с Google Sheets</b>\n\n"
        "Бот сравнит данные в таблице с текущими и обновит только изменения.\n\n"
        "✅ <b>Не затрагивается:</b>\n"
        "• Стоп/Go-статусы блюд\n"
        "• Загруженные фото блюд\n"
        "• Скачанные файлы обучения\n"
        "• Результаты тестов и прогресс\n"
        "• Привязки Telegram сотрудников\n\n"
        "Нажмите кнопку для начала синхронизации:",
        reply_markup=get_sync_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_sync:all")
async def sync_all(callback: CallbackQuery, user=None):
    """Выполнить полную синхронизацию"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    await callback.message.edit_text(
        "🔄 <b>Синхронизация запущена...</b>\n\n"
        "⏳ Подключение к Google Sheets...\n"
        "Пожалуйста, подождите.",
        parse_mode="HTML",
    )

    try:
        sync = GoogleSheetsSync()
        report = await sync.sync_all()
    except Exception as e:
        logger.error(f"Ошибка синхронизации: {e}")
        await callback.message.edit_text(
            f"❌ <b>Ошибка синхронизации</b>\n\n{str(e)}",
            reply_markup=get_sync_keyboard(),
            parse_mode="HTML",
        )
        return

    if not report.get("success"):
        error = report.get("error", "Неизвестная ошибка")
        await callback.message.edit_text(
            f"❌ <b>Ошибка синхронизации</b>\n\n{error}",
            reply_markup=get_sync_keyboard(),
            parse_mode="HTML",
        )
        return

    # Формируем отчёт
    details = report.get("details", {})
    text = "✅ <b>Синхронизация завершена!</b>\n\n"

    # Сотрудники
    emp = details.get("employees", {})
    if "error" in emp:
        text += f"👥 Сотрудники: ❌ {emp['error']}\n"
    else:
        text += (
            f"👥 Сотрудники: "
            f"создано {emp.get('created', 0)}, "
            f"обновлено {emp.get('updated', 0)}, "
            f"деактивировано {emp.get('deactivated', 0)}\n"
        )

    # Меню
    menu = details.get("menu", {})
    if "error" in menu:
        text += f"🍽 Меню: ❌ {menu['error']}\n"
    else:
        parts = []
        if menu.get("created"):
            parts.append(f"+{menu['created']} нов.")
        if menu.get("updated"):
            parts.append(f"⟳{menu['updated']} обн.")
        if menu.get("unchanged"):
            parts.append(f"{menu['unchanged']} без изм.")
        if menu.get("deleted"):
            parts.append(f"-{menu['deleted']} удал.")
        total = menu.get("created", 0) + menu.get("updated", 0) + menu.get("unchanged", 0)
        text += f"🍽 Меню ({total}): {', '.join(parts) if parts else 'нет данных'}\n"

    # Обучение
    training = details.get("training", {})
    if "error" in training:
        text += f"📚 Обучение: ❌ {training['error']}\n"
    else:
        parts = []
        if training.get("created"):
            parts.append(f"+{training['created']} нов.")
        if training.get("updated"):
            parts.append(f"⟳{training['updated']} обн.")
        if training.get("unchanged"):
            parts.append(f"{training['unchanged']} без изм.")
        if training.get("deleted"):
            parts.append(f"-{training['deleted']} удал.")
        if training.get("files_downloaded"):
            parts.append(f"📎{training['files_downloaded']} файлов")
        total = training.get("created", 0) + training.get("updated", 0) + training.get("unchanged", 0)
        text += f"📚 Обучение ({total}): {', '.join(parts) if parts else 'нет данных'}\n"

    # Тесты
    tests = details.get("tests", {})
    if "error" in tests:
        text += f"📝 Тесты: ❌ {tests['error']}\n"
    else:
        text += (
            f"📝 Тесты: {tests.get('tests', 0)} тестов, "
            f"{tests.get('questions', 0)} вопросов\n"
        )

    # Чек-листы
    checklists = details.get("checklists", {})
    if "error" in checklists:
        text += f"📋 Чек-листы: ❌ {checklists['error']}\n"
    else:
        text += f"📋 Чек-листы: загружено {checklists.get('count', 0)} задач\n"

    # Мотивация
    motivation = details.get("motivation", {})
    if "error" in motivation:
        text += f"💪 Мотивация: ❌ {motivation['error']}\n"
    else:
        text += f"💪 Мотивация: {motivation.get('count', 0)} сообщений\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_sync_keyboard(),
        parse_mode="HTML",
    )
