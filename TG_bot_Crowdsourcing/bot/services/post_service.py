"""
Сервис для работы с постами
"""
from datetime import datetime
from typing import List

from aiogram.types import Message, User
from bot.models.post import PostData
from bot.utils.helpers import generate_post_id
from data.storage import PostStorage
import asyncio
from ..database.user_service import UserService

class PostService:
    """Сервис для работы с постами"""
    
    @staticmethod
    def create_post(user: User, date: str, photos: List[str], videos: List[str],
                   location_name: str, location_description: str, coordinates: str) -> tuple[str, PostData]:
        """Создает новый пост"""
        post_data = PostData(
            user_id=user.id,
            username=user.username or user.first_name or "Unknown",
            date=date,
            photos=photos,
            videos=videos,  # Добавляем поддержку видео
            location_name=location_name,
            location_description=location_description,
            coordinates=coordinates,
            timestamp=datetime.now()
        )
        
        post_id = generate_post_id(user.id)
        PostStorage.add_post(post_id, post_data)
        
        # Асинхронно увеличиваем счетчик отправленных постов
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(UserService.increment_submitted_posts(user.id))
        except Exception as e:
            print(f"Ошибка обновления счетчика отправленных постов: {e}")
        
        return post_id, post_data
    
    @staticmethod
    def get_post(post_id: str) -> PostData | None:
        """Получает пост по ID"""
        return PostStorage.get_post(post_id)
    
    @staticmethod
    def delete_post(post_id: str) -> None:
        """Удаляет пост"""
        PostStorage.remove_post(post_id)
    
    @staticmethod
    def get_statistics() -> dict:
        """Получает статистику"""
        return {
            "total_posts": PostStorage.get_posts_count(),
            "unique_users": PostStorage.get_users_count(),
            "all_posts": PostStorage.get_all_posts()
        }