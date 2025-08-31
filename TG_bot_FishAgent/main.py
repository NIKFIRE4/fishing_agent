import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import os

# Импорт всех роутеров
from handlers.start import start_router
from handlers.search import search_router  
from handlers.navigation import navigation_router
from handlers.history import history_router
from handlers.callbacks import callbacks_router

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # Инициализация бота
    bot = Bot(
        token=os.getenv("TOKEN"),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Создание диспетчера
    dp = Dispatcher()
    
    # Регистрация роутеров
    dp.include_router(search_router)
    dp.include_router(history_router)
    dp.include_router(start_router)
    dp.include_router(navigation_router)
    
    dp.include_router(callbacks_router)
    
    logger.info("Бот запускается...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())