import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from handlers import base, schedule, homework, settings
from services.scheduler import start_background_tasks

# Конфигурация логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Подключаем наши "роутеры" (кусочки логики из других файлов)
    dp.include_router(base.router)
    dp.include_router(schedule.router)
    dp.include_router(homework.router)
    dp.include_router(settings.router)

    # Запускаем фоновые задачи
    start_background_tasks(bot, dp)

    # Запускаем бота (удаляем старые обновления, если бот долго лежал)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")