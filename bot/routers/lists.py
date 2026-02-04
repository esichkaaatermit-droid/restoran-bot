from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.database import async_session_maker
from database.repositories import MenuRepository
from database.models import MenuType
from bot.keyboards import get_back_keyboard

router = Router()


async def show_stop_list(message: Message, user):
    """Показать стоп-лист"""
    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        items = await menu_repo.get_stop_list(user.branch)
    
    if not items:
        await message.answer(
            "🚫 <b>Стоп-лист</b>\n\n"
            "Отличные новости! В данный момент стоп-лист пуст.\n"
            "Все позиции доступны для заказа.",
            parse_mode="HTML"
        )
        return
    
    # Группируем по типу меню и категории
    kitchen_items = {}
    bar_items = {}
    
    for item in items:
        if item.menu_type == MenuType.KITCHEN:
            if item.category not in kitchen_items:
                kitchen_items[item.category] = []
            kitchen_items[item.category].append(item)
        else:
            if item.category not in bar_items:
                bar_items[item.category] = []
            bar_items[item.category].append(item)
    
    text = "🚫 <b>Стоп-лист</b>\n\n"
    text += "<i>Следующие позиции временно недоступны:</i>\n\n"
    
    if kitchen_items:
        text += "🍳 <b>КУХНЯ</b>\n"
        for category, cat_items in kitchen_items.items():
            text += f"\n<b>{category}:</b>\n"
            for item in cat_items:
                text += f"  • {item.name}\n"
    
    if bar_items:
        if kitchen_items:
            text += "\n"
        text += "🍹 <b>БАР</b>\n"
        for category, cat_items in bar_items.items():
            text += f"\n<b>{category}:</b>\n"
            for item in cat_items:
                text += f"  • {item.name}\n"
    
    await message.answer(
        text,
        parse_mode="HTML"
    )


async def show_go_list(message: Message, user):
    """Показать go-лист"""
    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        items = await menu_repo.get_go_list(user.branch)
    
    if not items:
        await message.answer(
            "✅ <b>Go-лист</b>\n\n"
            "В данный момент нет приоритетных позиций для продажи.",
            parse_mode="HTML"
        )
        return
    
    # Группируем по типу меню и категории
    kitchen_items = {}
    bar_items = {}
    
    for item in items:
        if item.menu_type == MenuType.KITCHEN:
            if item.category not in kitchen_items:
                kitchen_items[item.category] = []
            kitchen_items[item.category].append(item)
        else:
            if item.category not in bar_items:
                bar_items[item.category] = []
            bar_items[item.category].append(item)
    
    text = "✅ <b>Go-лист</b>\n\n"
    text += "<i>🔥 Приоритетные позиции для продажи:</i>\n\n"
    
    if kitchen_items:
        text += "🍳 <b>КУХНЯ</b>\n"
        for category, cat_items in kitchen_items.items():
            text += f"\n<b>{category}:</b>\n"
            for item in cat_items:
                text += f"  🔥 {item.name} — {item.price:.0f} ₽\n"
    
    if bar_items:
        if kitchen_items:
            text += "\n"
        text += "🍹 <b>БАР</b>\n"
        for category, cat_items in bar_items.items():
            text += f"\n<b>{category}:</b>\n"
            for item in cat_items:
                text += f"  🔥 {item.name} — {item.price:.0f} ₽\n"
    
    text += "\n<i>Рекомендуйте эти позиции гостям!</i>"
    
    await message.answer(
        text,
        parse_mode="HTML"
    )
