"""Рассылка сообщений (админ)"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import async_session_maker
from database.repositories import UserRepository

router = Router()


class BroadcastStates(StatesGroup):
    message = State()


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext, user=None):
    """Начать рассылку"""
    await callback.answer()
    if not user or user.role.value != "manager":
        return

    await state.set_state(BroadcastStates.message)
    await callback.message.edit_text(
        "📢 <b>Рассылка</b>\n\n"
        "Отправьте текст или фото с подписью для рассылки.\n"
        "Сообщение получат все активные сотрудники с привязанным Telegram.",
        parse_mode="HTML",
    )


@router.message(BroadcastStates.message, F.text)
async def admin_broadcast_text(message: Message, state: FSMContext, user=None):
    """Рассылка текстового сообщения"""
    if not user or user.role.value != "manager":
        await state.clear()
        return

    await state.clear()

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        tg_users = await user_repo.get_all_with_telegram()

    sent = 0
    for tg_user in tg_users:
        try:
            await message.bot.send_message(
                tg_user.telegram_id,
                f"📢 <b>Объявление</b>\n\n{message.text}",
                parse_mode="HTML",
            )
            sent += 1
        except Exception:
            pass

    await message.answer(f"✅ Сообщение отправлено {sent} сотрудникам.")


@router.message(BroadcastStates.message, F.photo)
async def admin_broadcast_photo(message: Message, state: FSMContext, user=None):
    """Рассылка фото с подписью"""
    if not user or user.role.value != "manager":
        await state.clear()
        return

    await state.clear()

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        tg_users = await user_repo.get_all_with_telegram()

    photo_id = message.photo[-1].file_id
    caption = message.caption or ""

    sent = 0
    for tg_user in tg_users:
        try:
            await message.bot.send_photo(
                tg_user.telegram_id,
                photo=photo_id,
                caption=f"📢 <b>Объявление</b>\n\n{caption}",
                parse_mode="HTML",
            )
            sent += 1
        except Exception:
            pass

    await message.answer(f"✅ Фото отправлено {sent} сотрудникам.")
