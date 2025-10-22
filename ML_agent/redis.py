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
    
    def get_all_places(self) -> List[Dict]:
        """
        Получает все места из Redis кэша.
        
        Returns:
            Список мест с embeddings и координатами
        """
        try:
            cached = self.client.get('all_places')
            if cached:
                return json.loads(cached)
            return []
        except redis.RedisError as e:
            print(f"Ошибка Redis при получении мест: {e}")
            return []

    