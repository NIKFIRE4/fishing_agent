"""
Подключение к базе данных PostgreSQL
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from .models import Base
from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Создаем асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Установите True для отладки SQL запросов
    pool_size=10,
    max_overflow=20
)

# Создаем фабрику сессий
async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def create_tables():
    """Создает таблицы в базе данных"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Таблицы базы данных созданы успешно")
    except Exception as e:
        logger.error(f"Ошибка создания таблиц: {e}")
        raise

async def get_db_session():
    """Получает сессию базы данных"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка в сессии базы данных: {e}")
            raise
        finally:
            await session.close()

async def check_connection():
    """Проверяет подключение к базе данных"""
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                logger.info("Подключение к базе данных установлено успешно")
                return True
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return False
    
    return False

async def close_db():
    """Закрывает подключение к базе данных"""
    await engine.dispose()
    logger.info("Подключение к базе данных закрыто")