"""Загрузка фото блюд (админ)"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import async_session_maker
from database.repositories import MenuRepository
from bot.keyboards.admin_keyboards import get_photo_search_results_keyboard

router = Router()


class PhotoUploadStates(StatesGroup):
    search = State()
    upload = State()


@router.callback_query(F.data == "admin:photos")
async def admin_photos(callback: CallbackQuery, state: FSMContext, user=None):
    """Меню загрузки фото"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    await state.set_state(PhotoUploadStates.search)
    await callback.message.edit_text(
        "📸 <b>Фото блюд</b>\n\n"
        "Введите название блюда для поиска:",
        parse_mode="HTML",
    )


@router.message(PhotoUploadStates.search)
async def admin_photos_search(message: Message, state: FSMContext, user=None):
    """Поиск блюда для фото"""
    if not user or user.role.value != "manager":
        await state.clear()
        return

    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        items = await menu_repo.search_by_name(message.text.strip(), user.branch)

    await state.clear()

    if not items:
        await message.answer("❌ Ничего не найдено. Попробуйте другой запрос.")
        return

    await message.answer(
        f"📸 Найдено {len(items)} позиций.\n"
        "Выберите блюдо для загрузки фото:",
        reply_markup=get_photo_search_results_keyboard(items),
    )


@router.callback_query(F.data.startswith("admin_photo:select:"))
async def admin_photo_select(callback: CallbackQuery, state: FSMContext, user=None):
    """Выбрать блюдо для загрузки фото"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    item_id = int(callback.data.split(":")[-1])
    await state.update_data(item_id=item_id)
    await state.set_state(PhotoUploadStates.upload)

    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        item = await menu_repo.get_by_id(item_id)

    name = item.name if item else "Блюдо"
    await callback.message.edit_text(
        f"📸 Отправьте фото для <b>{name}</b>:",
        parse_mode="HTML",
    )


@router.message(PhotoUploadStates.upload, F.photo)
async def admin_photo_upload(message: Message, state: FSMContext, user=None):
    """Загрузить фото"""
    if not user or user.role.value != "manager":
        await state.clear()
        return

    data = await state.get_data()
    item_id = data.get("item_id")
    await state.clear()

    file_id = message.photo[-1].file_id

    async with async_session_maker() as session:
        menu_repo = MenuRepository(session)
        item = await menu_repo.update(item_id, photo=file_id)

    if item:
        await message.answer(
            f"✅ Фото для <b>{item.name}</b> сохранено!",
            parse_mode="HTML",
        )
    else:
        await message.answer("❌ Блюдо не найдено.")
