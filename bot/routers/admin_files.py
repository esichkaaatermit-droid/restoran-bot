"""Загрузка файлов обучения (админ)"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import async_session_maker
from database.repositories import TrainingRepository
from database.models import UserRole
from bot.utils import ROLE_NAMES

router = Router()


class FileUploadStates(StatesGroup):
    waiting_file = State()


@router.callback_query(F.data == "admin:files")
async def admin_files(callback: CallbackQuery, user=None):
    """Меню загрузки файлов обучения"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    async with async_session_maker() as session:
        training_repo = TrainingRepository(session)
        materials = await training_repo.get_all(branch=user.branch)

    if not materials:
        await callback.message.edit_text(
            "📄 Обучающих материалов пока нет.\n"
            "Сначала выполните синхронизацию из Google Sheets.",
            parse_mode="HTML",
        )
        return

    # Показываем материалы без файлов
    no_file = [m for m in materials if not m.file_path]

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    buttons = []
    for mat in no_file[:15]:
        role_short = {
            UserRole.HOSTESS: "Х",
            UserRole.WAITER: "О",
            UserRole.BARTENDER: "Б",
            UserRole.MANAGER: "М",
        }.get(mat.role, "?")
        buttons.append([
            InlineKeyboardButton(
                text=f"[{role_short}] {mat.title[:40]}",
                callback_data=f"admin_file:select:{mat.id}",
            )
        ])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")])

    text = (
        f"📄 <b>Файлы обучения</b>\n\n"
        f"Всего материалов: {len(materials)}\n"
        f"Без файлов: {len(no_file)}\n\n"
        "Выберите материал для загрузки файла:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_file:select:"))
async def admin_file_select(callback: CallbackQuery, state: FSMContext, user=None):
    """Выбрать материал для загрузки файла"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    material_id = int(callback.data.split(":")[-1])
    await state.update_data(material_id=material_id)
    await state.set_state(FileUploadStates.waiting_file)

    async with async_session_maker() as session:
        training_repo = TrainingRepository(session)
        material = await training_repo.get_material_by_id(material_id)

    name = material.title if material else "Материал"
    await callback.message.edit_text(
        f"📄 Отправьте документ или видео для:\n<b>{name}</b>",
        parse_mode="HTML",
    )


@router.message(FileUploadStates.waiting_file, F.document)
async def admin_file_upload_doc(message: Message, state: FSMContext, user=None):
    """Загрузить документ"""
    if not user or user.role.value != "manager":
        await state.clear()
        return

    data = await state.get_data()
    material_id = data.get("material_id")
    await state.clear()

    file_id = message.document.file_id

    async with async_session_maker() as session:
        training_repo = TrainingRepository(session)
        material = await training_repo.update(material_id, file_path=file_id)

    if material:
        await message.answer(
            f"✅ Документ привязан к <b>{material.title}</b>!",
            parse_mode="HTML",
        )
    else:
        await message.answer("❌ Материал не найден.")


@router.message(FileUploadStates.waiting_file, F.video)
async def admin_file_upload_video(message: Message, state: FSMContext, user=None):
    """Загрузить видео"""
    if not user or user.role.value != "manager":
        await state.clear()
        return

    data = await state.get_data()
    material_id = data.get("material_id")
    await state.clear()

    file_id = message.video.file_id

    async with async_session_maker() as session:
        training_repo = TrainingRepository(session)
        material = await training_repo.update(material_id, file_path=file_id)

    if material:
        await message.answer(
            f"✅ Видео привязано к <b>{material.title}</b>!",
            parse_mode="HTML",
        )
    else:
        await message.answer("❌ Материал не найден.")
