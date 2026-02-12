import asyncio
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config import settings
from .models import Base

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Получение сессии БД"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db(max_retries: int = 10, retry_delay: float = 3.0):
    """Инициализация БД - создание всех таблиц (с повторными попытками)"""
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("База данных инициализирована успешно")
            return
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Не удалось подключиться к БД после {max_retries} попыток: {e}")
                raise
            logger.warning(
                f"Попытка {attempt}/{max_retries} подключения к БД не удалась: {e}. "
                f"Повтор через {retry_delay}с..."
            )
            await asyncio.sleep(retry_delay)
