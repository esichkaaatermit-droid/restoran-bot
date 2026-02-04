from typing import Optional, List
import random

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import MotivationMessage


class MotivationRepository:
    """Репозиторий для работы с мотивационными сообщениями"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_random_message(self) -> Optional[MotivationMessage]:
        """Получить случайное мотивационное сообщение"""
        result = await self.session.execute(
            select(MotivationMessage)
            .where(MotivationMessage.is_active == True)
        )
        messages = list(result.scalars().all())
        
        if not messages:
            return None
        
        return random.choice(messages)
    
    async def get_all(self, only_active: bool = True) -> List[MotivationMessage]:
        """Получить все сообщения"""
        query = select(MotivationMessage)
        if only_active:
            query = query.where(MotivationMessage.is_active == True)
        query = query.order_by(MotivationMessage.id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(self, text: str) -> MotivationMessage:
        """Создать мотивационное сообщение"""
        message = MotivationMessage(text=text, is_active=True)
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message
    
    async def bulk_create(self, texts: List[str]) -> int:
        """Массовое создание сообщений"""
        for text in texts:
            message = MotivationMessage(text=text, is_active=True)
            self.session.add(message)
        await self.session.commit()
        return len(texts)
    
    async def update(self, message_id: int, text: str = None, is_active: bool = None) -> Optional[MotivationMessage]:
        """Обновить сообщение"""
        result = await self.session.execute(
            select(MotivationMessage).where(MotivationMessage.id == message_id)
        )
        message = result.scalar_one_or_none()
        
        if message:
            if text is not None:
                message.text = text
            if is_active is not None:
                message.is_active = is_active
            await self.session.commit()
            await self.session.refresh(message)
        
        return message
