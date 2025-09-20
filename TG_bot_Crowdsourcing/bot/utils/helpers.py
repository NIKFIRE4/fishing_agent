"""
Вспомогательные функции
"""
from datetime import datetime
from typing import Optional

def generate_post_id(user_id: int) -> str:
    """Генерирует уникальный ID для поста"""
    timestamp = int(datetime.now().timestamp())
    return f"{user_id}_{timestamp}"

def validate_date(date_string: str) -> Optional[datetime]:
    """Проверяет корректность формата даты"""
    try:
        return datetime.strptime(date_string, "%d.%m.%Y")
    except ValueError:
        return None

def format_coordinates(coordinates: str) -> str:
    """Форматирует координаты"""
    return coordinates.strip()

def truncate_text(text: str, max_length: int) -> str:
    """Обрезает текст до указанной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."