from typing import Optional, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, UserRole


class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по telegram_id"""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id, User.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def get_by_phone(self, phone: str) -> Optional[User]:
        """Получить пользователя по номеру телефона (без привязанного telegram_id)"""
        # Нормализуем номер телефона
        normalized_phone = self._normalize_phone(phone)
        
        result = await self.session.execute(
            select(User).where(
                User.phone == normalized_phone,
                User.telegram_id.is_(None),
                User.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_phone_any(self, phone: str) -> Optional[User]:
        """Получить пользователя по номеру телефона (любого)"""
        normalized_phone = self._normalize_phone(phone)
        
        result = await self.session.execute(
            select(User).where(User.phone == normalized_phone)
        )
        return result.scalar_one_or_none()
    
    async def bind_telegram(self, user_id: int, telegram_id: int) -> bool:
        """Привязать telegram_id к пользователю"""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(telegram_id=telegram_id)
        )
        await self.session.commit()
        return True
    
    async def get_all(self, role: Optional[UserRole] = None, branch: Optional[str] = None) -> List[User]:
        """Получить всех пользователей с фильтрами"""
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
        if branch:
            query = query.where(User.branch == branch)
        
        query = query.order_by(User.full_name)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(
        self,
        full_name: str,
        phone: str,
        role: UserRole,
        branch: str,
        telegram_id: Optional[int] = None
    ) -> User:
        """Создать нового пользователя"""
        user = User(
            full_name=full_name,
            phone=self._normalize_phone(phone),
            role=role,
            branch=branch,
            telegram_id=telegram_id,
            is_active=True
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Обновить данные пользователя"""
        if 'phone' in kwargs:
            kwargs['phone'] = self._normalize_phone(kwargs['phone'])
        
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(**kwargs)
        )
        await self.session.commit()
        
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_with_telegram(self) -> List[User]:
        """Получить всех активных пользователей с привязанным Telegram"""
        result = await self.session.execute(
            select(User).where(
                User.is_active == True,
                User.telegram_id.isnot(None),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Нормализация номера телефона"""
        # Убираем все символы кроме цифр
        digits = ''.join(filter(str.isdigit, phone))
        
        # Если начинается с 8, заменяем на 7
        if digits.startswith('8') and len(digits) == 11:
            digits = '7' + digits[1:]
        
        # Если 10 цифр, добавляем 7 в начало
        if len(digits) == 10:
            digits = '7' + digits
        
        return digits
