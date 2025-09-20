"""
Хранилище данных в памяти
"""
from typing import Dict
from bot.models.post import PostData

# Хранилище данных постов
pending_posts: Dict[str, PostData] = {}

class PostStorage:
    """Класс для работы с хранилищем постов"""
    
    @staticmethod
    def add_post(post_id: str, post_data: PostData) -> None:
        """Добавляет пост в хранилище"""
        pending_posts[post_id] = post_data
    
    @staticmethod
    def get_post(post_id: str) -> PostData | None:
        """Получает пост по ID"""
        return pending_posts.get(post_id)
    
    @staticmethod
    def remove_post(post_id: str) -> None:
        """Удаляет пост из хранилища"""
        if post_id in pending_posts:
            del pending_posts[post_id]
    
    @staticmethod
    def get_all_posts() -> Dict[str, PostData]:
        """Возвращает все посты"""
        return pending_posts.copy()
    
    @staticmethod
    def get_posts_count() -> int:
        """Возвращает количество постов на модерации"""
        return len(pending_posts)
    
    @staticmethod
    def get_users_count() -> int:
        """Возвращает количество уникальных пользователей"""
        return len(set(post.user_id for post in pending_posts.values()))