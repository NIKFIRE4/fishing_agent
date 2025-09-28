"""
Сервис модерации постов
"""
import logging
from typing import List

from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo

from bot.models.post import PostData
from bot.keyboards.admin_keyboards import get_moderation_keyboard
from bot.services.post_service import PostService
from config import ADMIN_ID, CHANNEL_ID, MESSAGES
from ..database.user_service import UserService

logger = logging.getLogger(__name__)

class ModerationService:
    """Сервис для модерации постов"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def send_to_moderation(self, post_id: str, post_data: PostData) -> None:
        """Добавляет пост в тихую очередь модерации (без уведомлений)"""
        # Пост уже добавлен в хранилище в PostService.create_post()
        # Просто логируем добавление в очередь
        logger.info(f"Пост {post_id} от пользователя {post_data.username} добавлен в очередь модерации")
    
    async def approve_post(self, post_id: str) -> bool:
        """Одобряет пост и публикует в канале"""
        post_data = PostService.get_post(post_id)
        if not post_data:
            return False
        
        try:
            channel_text = post_data.to_channel_text()
            
            
            # Получаем все медиафайлы
            photos = post_data.photos or []
            videos = getattr(post_data, 'videos', []) or []
            total_media = len(photos) + len(videos)
            
            # Если медиафайлов нет
            if total_media == 0:
                # Отправляем только текст
                await self.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=channel_text,
                    parse_mode="HTML"
                )
            # Если всего один медиафайл
            elif total_media == 1:
                if photos:
                    # Одно фото
                    await self.bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=photos[0],
                        caption=channel_text,
                        parse_mode="HTML"
                    )
                else:
                    # Одно видео
                    await self.bot.send_video(
                        chat_id=CHANNEL_ID,
                        video=videos[0],
                        caption=channel_text,
                        parse_mode="HTML"
                    )
            else:
                # Создаем медиа-группу из фото и видео
                media = []
                caption_added = False
                
                # Добавляем фото
                for photo_id in photos:
                    if not caption_added:
                        media.append(InputMediaPhoto(media=photo_id, caption=channel_text, parse_mode="HTML"))
                        caption_added = True
                    else:
                        media.append(InputMediaPhoto(media=photo_id))
                
                # Добавляем видео
                for video_id in videos:
                    if not caption_added:
                        media.append(InputMediaVideo(media=video_id, caption=channel_text, parse_mode="HTML"))
                        caption_added = True
                    else:
                        media.append(InputMediaVideo(media=video_id))
                
                await self.bot.send_media_group(
                    chat_id=CHANNEL_ID,
                    media=media
                )
            
            await UserService.increment_published_posts(post_data.user_id)
            
            # Уведомляем автора
            await self.bot.send_message(
                chat_id=post_data.user_id,
                text=MESSAGES["post_approved"]
            )
            
            # Удаляем из очереди
            PostService.delete_post(post_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка публикации поста {post_id}: {e}")
            print(f"DEBUG: Ошибка публикации: {e}")
            return False
    
    async def reject_post(self, post_id: str) -> bool:
        """Отклоняет пост"""
        post_data = PostService.get_post(post_id)
        if not post_data:
            return False
        
        try:
            # Уведомляем автора
            await self.bot.send_message(
                chat_id=post_data.user_id,
                text=MESSAGES["post_rejected"]
            )
            
            # Удаляем из очереди
            PostService.delete_post(post_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отклонения поста {post_id}: {e}")
            return False
    
    async def request_edit(self, post_id: str) -> bool:
        """Запрашивает правки от автора"""
        post_data = PostService.get_post(post_id)
        if not post_data:
            return False
        
        try:
            # Уведомляем автора
            await self.bot.send_message(
                chat_id=post_data.user_id,
                text=MESSAGES["post_needs_edit"]
            )
            
            # Пост остается в очереди для повторной отправки
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запроса правок для поста {post_id}: {e}")
            return False