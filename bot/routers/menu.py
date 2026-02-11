from pathlib import Path

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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
)
from bot.utils import safe_edit_or_send

router = Router()

# Папка для фото блюд
PHOTOS_DIR = Path(__file__).parent.parent.parent / "photos"


class MenuPhotoUploadStates(StatesGroup):
    waiting_photo = State()


@router.callback_query(F.data.startswith("menu_type:"))
async def select_menu_type(callback: CallbackQuery, user=None):
    """Выбор типа меню (кухня/бар)"""
    await callback.answer()
    
    if not user:
        await callback.message.answer("Пожалуйста, используйте /start для авторизации.")
        return
    
    menu_type = callback.data.split(":")[1]
    menu_type_enum = MenuType.KITCHEN if menu_type == "kitchen" else MenuType.BAR
    emoji = "🍳" if menu_type == "kitchen" else "🍹"
    label = "Меню кухни" if menu_type == "kitchen" else "Меню бара"

    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        categories = await menu_repo.get_categories(menu_type_enum, user.branch)

    if not categories:
        await safe_edit_or_send(
            callback,
            f"{emoji} {label}\n\nВ этом разделе пока нет позиций.",
            reply_markup=get_back_keyboard("menu_back_to_types"),
        )
        return

    await safe_edit_or_send(
        callback,
        f"{emoji} {label}\n\nВыберите категорию:",
        reply_markup=get_categories_keyboard(categories, menu_type),
    )


@router.callback_query(F.data == "menu_back_to_types")
async def back_to_menu_types(callback: CallbackQuery, user=None):
    """Возврат к выбору типа меню"""
    await callback.answer()
    
    await safe_edit_or_send(
        callback,
        "Выберите раздел меню:",
        reply_markup=get_menu_type_keyboard(),
    )


@router.callback_query(F.data.startswith("menu_back_to_categories:"))
async def back_to_categories(callback: CallbackQuery, user=None):
    """Возврат к категориям"""
    await callback.answer()
    
    if not user:
        return
    
    menu_type = callback.data.split(":")[1]
    menu_type_enum = MenuType.KITCHEN if menu_type == "kitchen" else MenuType.BAR
    emoji = "🍳" if menu_type == "kitchen" else "🍹"
    label = "Меню кухни" if menu_type == "kitchen" else "Меню бара"

    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        categories = await menu_repo.get_categories(menu_type_enum, user.branch)

    await safe_edit_or_send(
        callback,
        f"{emoji} {label}\n\nВыберите категорию:",
        reply_markup=get_categories_keyboard(categories, menu_type),
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
            categories = await menu_repo.get_categories(menu_type_enum, user.branch)
    
    if not items:
        await safe_edit_or_send(
            callback,
            f"В категории «{category}» пока нет доступных позиций.",
            reply_markup=get_categories_keyboard(categories, menu_type),
        )
        return
    
    await safe_edit_or_send(
        callback,
        f"📋 {category}\n\nВыберите позицию:",
        reply_markup=get_items_keyboard(items, menu_type, category),
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
        await safe_edit_or_send(
            callback,
            "Позиция не найдена.",
            reply_markup=get_back_keyboard("menu_back_to_types"),
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
    is_manager = user and user.role.value == "manager"
    kb = get_item_back_keyboard(menu_type, item.category, item_id=item.id, is_manager=is_manager)
    
    # Если есть фото — отправляем с фото
    if item.photo:
        photo_path = Path(item.photo)
        if photo_path.exists():
            from aiogram.exceptions import TelegramBadRequest
            try:
                await callback.message.delete()
            except TelegramBadRequest:
                pass
            await callback.message.answer_photo(
                photo=FSInputFile(photo_path),
                caption=card_text,
                reply_markup=kb,
                parse_mode="HTML"
            )
        else:
            await safe_edit_or_send(callback, card_text, reply_markup=kb)
    else:
        await safe_edit_or_send(callback, card_text, reply_markup=kb)


# ========== ЗАГРУЗКА ФОТО ИЗ КАРТОЧКИ БЛЮДА ==========

@router.callback_query(F.data.startswith("menu_upload_photo:"))
async def menu_upload_photo_start(callback: CallbackQuery, state: FSMContext, user=None):
    """Начать загрузку фото из карточки блюда"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    item_id = int(callback.data.split(":")[1])

    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        item = await menu_repo.get_by_id(item_id)

    if not item:
        await callback.message.answer("❌ Блюдо не найдено.")
        return

    await state.update_data(photo_item_id=item_id, photo_item_name=item.name,
                            photo_menu_type="kitchen" if item.menu_type == MenuType.KITCHEN else "bar",
                            photo_category=item.category)
    await state.set_state(MenuPhotoUploadStates.waiting_photo)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_photo_cancel:{item_id}")]
    ])

    await callback.message.answer(
        f"📸 Отправьте фото для <b>{item.name}</b>:",
        reply_markup=cancel_kb,
        parse_mode="HTML",
    )


@router.message(MenuPhotoUploadStates.waiting_photo, F.photo)
async def menu_upload_photo_receive(message: Message, state: FSMContext, user=None):
    """Получить и сохранить фото блюда"""
    if not user or user.role.value != "manager":
        await state.clear()
        return

    data = await state.get_data()
    item_id = data.get("photo_item_id")
    item_name = data.get("photo_item_name", "Блюдо")
    await state.clear()

    # Получаем файл
    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)

    # Создаём папку для фото, если её нет
    PHOTOS_DIR.mkdir(exist_ok=True)

    # Скачиваем фото
    file_path = PHOTOS_DIR / f"{item_id}.jpg"
    await message.bot.download_file(file.file_path, file_path)

    # Сохраняем путь в базу данных
    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        item = await menu_repo.update(item_id, photo=str(file_path))

    if item:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к блюду", callback_data=f"item:{item_id}")]
        ])
        await message.answer(
            f"✅ Фото для <b>{item_name}</b> сохранено!",
            reply_markup=back_kb,
            parse_mode="HTML",
        )
    else:
        await message.answer("❌ Блюдо не найдено.")


@router.callback_query(F.data.startswith("menu_photo_cancel:"))
async def menu_upload_photo_cancel(callback: CallbackQuery, state: FSMContext, user=None):
    """Отмена загрузки фото"""
    await callback.answer()
    await state.clear()
    item_id = int(callback.data.split(":")[1])
    await callback.message.edit_text("❌ Загрузка фото отменена.")

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к блюду", callback_data=f"item:{item_id}")]
    ])
    await callback.message.edit_text(
        "❌ Загрузка фото отменена.",
        reply_markup=back_kb,
    )


@router.message(MenuPhotoUploadStates.waiting_photo)
async def menu_upload_photo_invalid(message: Message, state: FSMContext, user=None):
    """Если отправлено не фото"""
    if message.text and message.text.lower() == "/cancel":
        await state.clear()
        await message.answer("❌ Загрузка фото отменена.")
        return

    await message.answer("📸 Пожалуйста, отправьте фото (изображение).")
