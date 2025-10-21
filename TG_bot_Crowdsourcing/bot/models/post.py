"""
Модель данных поста
"""
from dataclasses import dataclass
from datetime import datetime
from typing import *
from aiogram import html

@dataclass
class PostData:
    """Структура данных поста"""
    user_id: int
    username: Optional[str]
    date: Optional[str]                     # дата в строке, например "15.09.2025"
    photos: List[str]                       # список file_id фото
    videos: List[str]                       # список file_id видео (ДОБАВЛЕНО)
    location_name: Optional[str] = None     # название места (добавлено)
    location_description: Optional[str] = None
    coordinates: Optional[str] = None
    timestamp: datetime = datetime.now()

    def to_channel_text(self) -> str:
        """Форматирует текст для публикации в канале."""
        parts = []

        # Дата с подчеркиванием
        if self.date:
            parts.append(f"<u>{html.quote(self.date)}</u>")
        else:
            parts.append("<u>—</u>")

        # Название места между стикерами палаток
        if self.location_name:
            parts.append(f"🏕 {html.quote(self.location_name)} 🏕")

        # Описание
        if self.location_description:
            parts.append(html.quote(self.location_description))

        # Координаты в моноширинном шрифте
        if self.coordinates:
            parts.append(f"<code>{html.quote(self.coordinates)}</code>")

        return "\n".join(parts)
    
    def to_moderation_text(self) -> str:
        """Форматирует текст для модерации"""
        # Формируем информацию о медиафайлах
        media_info = []
        if self.photos:
            media_info.append(f"{len(self.photos)} фото")
        if self.videos:
            media_info.append(f"{len(self.videos)} видео")
        
        media_text = " и ".join(media_info) if media_info else "нет медиафайлов"
        
        return (
            f"🔍 НОВЫЙ ПОСТ НА МОДЕРАЦИЮ\n\n"
            f"👤 Автор: @{self.username} (ID: {self.user_id})\n"
            f"📅 Дата похода: {self.date}\n"
            f"📍 Место: {self.location_name}\n"
            f"📝 Описание: {self.location_description[:200]}{'...' if len(self.location_description or '') > 200 else ''}\n"
            f"🗺️ Координаты: {self.coordinates}\n"
            f"📸 Медиафайлы: {media_text}\n"
            f"🕐 Создано: {self.timestamp.strftime('%d.%m.%Y %H:%M')}"
        )