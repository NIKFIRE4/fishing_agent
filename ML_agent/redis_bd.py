import redis
import json
import os
from typing import List, Dict, Optional

class RedisManager:
    """Менеджер для работы с Redis"""
    
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            password=os.getenv('REDIS_PASSWORD', '1lomalsteklo'),
            decode_responses=True
        )
    
    def get_all_places(self, type_of_relax: Optional[str] = None) -> List[Dict]:
        """
        Получает все места из Redis кэша с опциональной фильтрацией по типу отдыха.
        
        Args:
            type_of_relax: Тип отдыха для фильтрации. Если None, возвращает все места.
        
        Returns:
            Список мест с embeddings и координатами
        """
        try:
            cached = self.client.get('all_places')
            if cached:
                all_places = json.loads(cached)
                
                # Если type_of_relax не указан, возвращаем все места
                if type_of_relax is None:
                    return all_places
                
                # Фильтруем места по type_of_relax
                filtered_places = [
                    place for place in all_places 
                    if place.get('type_of_relax') == type_of_relax
                ]
                
                return filtered_places
            return []
        except redis.RedisError as e:
            print(f"Ошибка Redis при получении мест: {e}")
            return []
    