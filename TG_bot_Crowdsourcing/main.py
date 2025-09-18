"""
Главный файл запуска бота Camp Place
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла ПЕРВЫМ ДЕЛОМ
load_dotenv()

# Добавляем корневую папку в путь для импортов
sys.path.append(str(Path(__file__).parent))

from config import BOT_TOKEN
from bot.handlers import common_handlers, user_handlers, admin_handlers

# Настройка логирования с поддержкой UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)



async def main():
    """Главная функция запуска бота"""
    
    # Проверяем токен
    if not BOT_TOKEN:
        logger.error("Не указан токен бота! Установите BOT_TOKEN в config.py или .env файле")
        return
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключаем роутеры обработчиков В ПРАВИЛЬНОМ ПОРЯДКЕ
    # Сначала специфичные обработчики
    dp.include_router(admin_handlers.router)
    dp.include_router(common_handlers.router)  
    # В конце - пользовательские с fallback обработчиком
    dp.include_router(user_handlers.router)
    
    logger.info("Бот Camp Place запускается...")
    
    try:
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"Бот @{bot_info.username} успешно запущен!")
        
        # Запускаем polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")