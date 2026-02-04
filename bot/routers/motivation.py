from aiogram import Router
from aiogram.types import Message

from database.database import async_session_maker
from database.repositories import MotivationRepository

router = Router()


async def show_motivation(message: Message, user):
    """Показать мотивационное сообщение"""
    async with async_session_maker() as session:
        motivation_repo = MotivationRepository(session)
        motivation = await motivation_repo.get_random_message()
    
    if not motivation:
        # Если нет сообщений в БД, показываем дефолтное
        default_messages = [
            "💪 Вы делаете отличную работу! Каждый гость уходит довольным благодаря Вам.",
            "🌟 Ваш профессионализм — это то, что делает наш ресторан особенным!",
            "✨ Помните: улыбка и внимание к деталям — ключ к успеху!",
        ]
        import random
        text = random.choice(default_messages)
    else:
        text = motivation.text
    
    await message.answer(
        f"💪 <b>Мотивация дня</b>\n\n"
        f"{text}",
        parse_mode="HTML"
    )
