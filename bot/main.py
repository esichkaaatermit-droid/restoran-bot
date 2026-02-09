import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from database.database import init_db
from bot.routers import setup_routers
from bot.middlewares import AuthMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def auto_sync():
    """Автоматическая синхронизация из Google Sheets"""
    try:
        from integrations.google_sheets import GoogleSheetsSync
        sync = GoogleSheetsSync()
        report = await sync.sync_all()
        if report.get("success"):
            logger.info("Автосинхронизация завершена успешно")
        else:
            logger.warning(f"Автосинхронизация: {report.get('error')}")
    except Exception as e:
        logger.error(f"Ошибка автосинхронизации: {e}")


async def main():
    """Запуск бота"""
    logger.info("Запуск бота...")

    # Инициализация БД
    logger.info("Инициализация базы данных...")
    await init_db()

    # Создание бота и диспетчера
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Подключение middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Подключение роутеров
    dp.include_router(setup_routers())

    # Планировщик автосинхронизации
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(auto_sync, "cron", hour=settings.AUTO_SYNC_HOUR, minute=0)
    scheduler.start()
    logger.info(f"Автосинхронизация запланирована на {settings.AUTO_SYNC_HOUR}:00 MSK")

    # Запуск polling
    logger.info("Бот запущен и готов к работе!")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
