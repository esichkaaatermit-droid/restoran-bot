from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.database import async_session_maker
from database.repositories import TrainingRepository
from bot.keyboards import (
    get_training_materials_keyboard,
    get_mark_completed_keyboard,
    get_back_keyboard,
)

router = Router()


async def show_training_materials(message: Message, user):
    """Показать список обучающих материалов"""
    async with async_session_maker() as session:
        training_repo = TrainingRepository(session)
        materials = await training_repo.get_materials_by_role(user.role, user.branch)
    
    if not materials:
        await message.answer(
            "Для Вашей должности пока нет обучающих материалов.\n"
            "Пожалуйста, обратитесь к менеджеру."
        )
        return
    
    await message.answer(
        "📚 <b>Обучающие материалы</b>\n\n"
        "Выберите тему для изучения:",
        reply_markup=get_training_materials_keyboard(materials),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("training:"))
async def show_material(callback: CallbackQuery, user=None):
    """Показать обучающий материал"""
    await callback.answer()
    
    if not user:
        await callback.message.answer("Пожалуйста, используйте /start для авторизации.")
        return
    
    material_id = int(callback.data.split(":")[1])
    
    async with async_session_maker() as session:
        training_repo = TrainingRepository(session)
        material = await training_repo.get_material_by_id(material_id)
        
        if not material:
            await callback.message.edit_text(
                "Материал не найден.",
                reply_markup=get_back_keyboard("training_back_to_list")
            )
            return
        
        # Проверяем прогресс
        progress = await training_repo.get_progress(user.id, material_id)
    
    # Формируем сообщение с материалом
    text = f"📖 <b>{material.title}</b>\n\n"
    
    if material.description:
        text += f"<i>{material.description}</i>\n\n"
    
    text += f"{material.content}"
    
    if progress and progress.is_completed:
        text += "\n\n✅ <i>Вы уже изучили этот материал</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_mark_completed_keyboard(material_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("training_complete:"))
async def mark_completed(callback: CallbackQuery, user=None):
    """Отметить материал как изученный"""
    await callback.answer("Отмечено как изученное ✅")
    
    if not user:
        return
    
    material_id = int(callback.data.split(":")[1])
    
    async with async_session_maker() as session:
        training_repo = TrainingRepository(session)
        await training_repo.mark_completed(user.id, material_id)
        material = await training_repo.get_material_by_id(material_id)
    
    if material:
        text = f"📖 <b>{material.title}</b>\n\n"
        
        if material.description:
            text += f"<i>{material.description}</i>\n\n"
        
        text += f"{material.content}"
        text += "\n\n✅ <i>Вы изучили этот материал</i>"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_mark_completed_keyboard(material_id),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "training_back_to_list")
async def back_to_training_list(callback: CallbackQuery, user=None):
    """Вернуться к списку материалов"""
    await callback.answer()
    
    if not user:
        return
    
    async with async_session_maker() as session:
        training_repo = TrainingRepository(session)
        materials = await training_repo.get_materials_by_role(user.role, user.branch)
    
    if not materials:
        await callback.message.edit_text(
            "Для Вашей должности пока нет обучающих материалов.",
            reply_markup=get_back_keyboard("back_to_main")
        )
        return
    
    await callback.message.edit_text(
        "📚 <b>Обучающие материалы</b>\n\n"
        "Выберите тему для изучения:",
        reply_markup=get_training_materials_keyboard(materials),
        parse_mode="HTML"
    )
