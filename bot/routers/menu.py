from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.database import async_session_maker
from database.repositories import MenuRepository
from database.models import MenuType
from bot.keyboards import (
    get_menu_type_keyboard,
    get_categories_keyboard,
    get_items_keyboard,
    get_back_keyboard,
)
from bot.keyboards.keyboards import (
    get_item_back_keyboard,
    get_kitchen_categories_keyboard,
    get_bar_categories_keyboard,
)

router = Router()


@router.callback_query(F.data.startswith("menu_type:"))
async def select_menu_type(callback: CallbackQuery, user=None):
    """Выбор типа меню (кухня/бар)"""
    await callback.answer()
    
    if not user:
        await callback.message.answer("Пожалуйста, используйте /start для авторизации.")
        return
    
    menu_type = callback.data.split(":")[1]
    
    if menu_type == "kitchen":
        await callback.message.edit_text(
            "🍳 Меню кухни\n\nВыберите категорию:",
            reply_markup=get_kitchen_categories_keyboard()
        )
    else:
        await callback.message.edit_text(
            "🍹 Меню бара\n\nВыберите категорию:",
            reply_markup=get_bar_categories_keyboard()
        )


@router.callback_query(F.data == "menu_back_to_types")
async def back_to_menu_types(callback: CallbackQuery, user=None):
    """Возврат к выбору типа меню"""
    await callback.answer()
    
    await callback.message.edit_text(
        "Выберите раздел меню:",
        reply_markup=get_menu_type_keyboard()
    )


@router.callback_query(F.data.startswith("menu_back_to_categories:"))
async def back_to_categories(callback: CallbackQuery, user=None):
    """Возврат к категориям"""
    await callback.answer()
    
    if not user:
        return
    
    menu_type = callback.data.split(":")[1]
    
    if menu_type == "kitchen":
        await callback.message.edit_text(
            "🍳 Меню кухни\n\nВыберите категорию:",
            reply_markup=get_kitchen_categories_keyboard()
        )
    else:
        await callback.message.edit_text(
            "🍹 Меню бара\n\nВыберите категорию:",
            reply_markup=get_bar_categories_keyboard()
        )


@router.callback_query(F.data.startswith("category:"))
async def select_category(callback: CallbackQuery, user=None):
    """Выбор категории"""
    await callback.answer()
    
    if not user:
        return
    
    parts = callback.data.split(":", 2)
    menu_type = parts[1]
    category = parts[2]
    
    menu_type_enum = MenuType.KITCHEN if menu_type == "kitchen" else MenuType.BAR
    
    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        items = await menu_repo.get_items_by_category(category, menu_type_enum, user.branch)
    
    if not items:
        if menu_type == "kitchen":
            keyboard = get_kitchen_categories_keyboard()
        else:
            keyboard = get_bar_categories_keyboard()
        await callback.message.edit_text(
            f"В категории «{category}» пока нет доступных позиций.",
            reply_markup=keyboard
        )
        return
    
    await callback.message.edit_text(
        f"📋 {category}\n\nВыберите позицию:",
        reply_markup=get_items_keyboard(items, menu_type, category)
    )


@router.callback_query(F.data.startswith("item:"))
async def show_item(callback: CallbackQuery, user=None):
    """Показать карточку позиции меню"""
    await callback.answer()
    
    if not user:
        return
    
    item_id = int(callback.data.split(":")[1])
    
    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        item = await menu_repo.get_by_id(item_id)
    
    if not item:
        await callback.message.edit_text(
            "Позиция не найдена.",
            reply_markup=get_back_keyboard("menu_back_to_types")
        )
        return
    
    # Формируем карточку
    status_label = ""
    if item.status.value == "go":
        status_label = "🔥 ПРИОРИТЕТНАЯ ПОЗИЦИЯ\n\n"
    
    card_text = f"{status_label}🍽 <b>{item.name}</b>\n\n"
    
    if item.description:
        card_text += f"📝 {item.description}\n\n"
    
    if item.composition:
        card_text += f"🥗 <b>Состав:</b> {item.composition}\n\n"
    
    if item.weight_volume:
        card_text += f"⚖️ <b>Объём/вес:</b> {item.weight_volume}\n"
    
    card_text += f"💰 <b>Цена:</b> {item.price:.0f} ₽"
    
    menu_type = "kitchen" if item.menu_type == MenuType.KITCHEN else "bar"
    
    await callback.message.edit_text(
        card_text,
        reply_markup=get_item_back_keyboard(menu_type, item.category),
        parse_mode="HTML"
    )
