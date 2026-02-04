from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from database.database import async_session_maker
from database.repositories import UserRepository


class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки авторизации пользователя"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем telegram_id из события
        telegram_id = None
        if isinstance(event, Message):
            telegram_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            telegram_id = event.from_user.id if event.from_user else None
        
        if telegram_id:
            async with async_session_maker() as session:
                user_repo = UserRepository(session)
                user = await user_repo.get_by_telegram_id(telegram_id)
                data["user"] = user
                data["db_session"] = session
        else:
            data["user"] = None
            data["db_session"] = None
        
        return await handler(event, data)
