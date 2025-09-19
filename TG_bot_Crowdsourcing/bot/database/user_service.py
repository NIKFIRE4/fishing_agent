"""
Сервис для работы с пользователями в базе данных
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.dialects.postgresql import insert
from aiogram.types import User as TelegramUser
from .models import User
from .database import async_session_maker


logger = logging.getLogger(__name__)

class UserService:
    """Сервис для работы с пользователями"""
    
    @staticmethod
    async def get_or_create_user(telegram_user: TelegramUser) -> User:
        """Получает пользователя из БД или создает нового"""
        async with async_session_maker() as session:
            try:
                # Пытаемся найти существующего пользователя
                result = await session.execute(
                    select(User).where(User.user_id == telegram_user.id)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    # Обновляем информацию о пользователе и последнюю активность
                    user.username = telegram_user.username
                    user.first_name = telegram_user.first_name
                    user.last_name = telegram_user.last_name
                    user.last_activity = datetime.now()
                    await session.commit()
                    return user
                else:
                    # Создаем нового пользователя
                    new_user = User(
                        user_id=telegram_user.id,
                        username=telegram_user.username,
                        first_name=telegram_user.first_name,
                        last_name=telegram_user.last_name,
                        registration_date=datetime.now(),
                        last_activity=datetime.now()
                    )
                    session.add(new_user)
                    await session.commit()
                    await session.refresh(new_user)
                    logger.info(f"Создан новый пользователь: {telegram_user.id} (@{telegram_user.username})")
                    return new_user
                    
            except Exception as e:
                await session.rollback()
                logger.error(f"Ошибка при работе с пользователем {telegram_user.id}: {e}")
                raise
    
    @staticmethod
    async def increment_submitted_posts(user_id: int) -> bool:
        """Увеличивает счетчик отправленных постов на модерацию"""
        async with async_session_maker() as session:
            try:
                await session.execute(
                    update(User)
                    .where(User.user_id == user_id)
                    .values(submitted_posts_count=User.submitted_posts_count + 1)
                )
                await session.commit()
                logger.info(f"Увеличен счетчик отправленных постов для пользователя {user_id}")
                return True
            except Exception as e:
                await session.rollback()
                logger.error(f"Ошибка увеличения счетчика отправленных постов для {user_id}: {e}")
                return False
    
    @staticmethod
    async def increment_published_posts(user_id: int) -> bool:
        """Увеличивает счетчик опубликованных постов"""
        async with async_session_maker() as session:
            try:
                await session.execute(
                    update(User)
                    .where(User.user_id == user_id)
                    .values(posts_count=User.posts_count + 1)
                )
                await session.commit()
                logger.info(f"Увеличен счетчик опубликованных постов для пользователя {user_id}")
                return True
            except Exception as e:
                await session.rollback()
                logger.error(f"Ошибка увеличения счетчика опубликованных постов для {user_id}: {e}")
                return False
    
    @staticmethod
    async def get_user_stats(user_id: int) -> Optional[Dict[str, Any]]:
        """Получает статистику пользователя"""
        async with async_session_maker() as session:
            try:
                result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    return {
                        "user_id": user.user_id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "registration_date": user.registration_date,
                        "posts_count": user.posts_count,
                        "submitted_posts_count": user.submitted_posts_count,
                        "last_activity": user.last_activity
                    }
                return None
            except Exception as e:
                logger.error(f"Ошибка получения статистики пользователя {user_id}: {e}")
                return None
    
    @staticmethod
    async def get_all_users_stats() -> Dict[str, Any]:
        """Получает общую статистику по всем пользователям"""
        async with async_session_maker() as session:
            try:
                # Общее количество пользователей
                total_users_result = await session.execute(select(func.count(User.id)))
                total_users = total_users_result.scalar() or 0

                # Пользователи, зарегистрированные за последние 30 дней
                thirty_days_ago = datetime.now() - timedelta(days=30)
                recent_users_result = await session.execute(
                    select(func.count(User.id)).where(User.registration_date >= thirty_days_ago)
                )
                recent_users = recent_users_result.scalar() or 0

                # Общее количество опубликованных постов
                total_posts_result = await session.execute(select(func.coalesce(func.sum(User.posts_count), 0)))
                total_posts = int(total_posts_result.scalar() or 0)

                # Общее количество отправленных постов
                total_submitted_result = await session.execute(select(func.coalesce(func.sum(User.submitted_posts_count), 0)))
                total_submitted = int(total_submitted_result.scalar() or 0)

                # Топ пользователей по количеству постов
                top_users_result = await session.execute(
                    select(User.username, User.first_name, User.posts_count)
                    .where(User.posts_count > 0)
                    .order_by(User.posts_count.desc())
                    .limit(10)
                )
                top_users_rows = top_users_result.fetchall()

                top_users = []
                for row in top_users_rows:
                    # row — namedtuple-like: (username, first_name, posts_count)
                    username = row[0] or row[1] or "Unknown"
                    posts_count = int(row[2] or 0)
                    top_users.append({"username": username, "posts_count": posts_count})

                approval_rate = round((total_posts / max(total_submitted, 1)) * 100, 1)

                return {
                    "total_users": int(total_users),
                    "recent_users": int(recent_users),
                    "total_posts": total_posts,
                    "total_submitted": total_submitted,
                    "approval_rate": approval_rate,
                    "top_users": top_users
                }

            except Exception as e:
                logger.error(f"Ошибка получения общей статистики: {e}")
                return {
                    "total_users": 0,
                    "recent_users": 0,
                    "total_posts": 0,
                    "total_submitted": 0,
                    "approval_rate": 0,
                    "top_users": []
                }
        
    @staticmethod
    async def get_recent_users(limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список недавно зарегистрированных пользователей"""
        async with async_session_maker() as session:
            try:
                result = await session.execute(
                    select(User)
                    .order_by(User.registration_date.desc())
                    .limit(limit)
                )
                users = result.scalars().all()
                
                return [
                    {
                        "user_id": user.user_id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "registration_date": user.registration_date,
                        "posts_count": user.posts_count,
                        "submitted_posts_count": user.submitted_posts_count
                    }
                    for user in users
                ]
            except Exception as e:
                logger.error(f"Ошибка получения недавних пользователей: {e}")
                return []