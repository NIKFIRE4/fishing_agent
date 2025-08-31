
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp
from aiogram import types
from aiogram.types import InputMediaPhoto, InputFile, CallbackQuery, FSInputFile
from dotenv import load_dotenv
from typing import Optional, List, Dict
import logging
import asyncio
import os
from urllib.parse import quote
from database.requests import get_or_create_user, save_selected_spot, get_user_fishing_history
load_dotenv()
logger = logging.getLogger(__name__)


class MLServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def search_fishing_spots(self, user_id: int, query: str) -> dict:
        """Вызов вашего ML сервиса для поиска мест рыбалки"""
        url = f"{self.base_url}/telegram/search"
        
        payload = {
            "user_id": user_id,
            "query": query,
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"ML service error: {response.status} - {error_text}")
                        return {"success": False, "message": "Service unavailable"}
        except asyncio.TimeoutError:
            logger.error("ML service timeout")
            return {"success": False, "message": "Service timeout"}
        except Exception as e:
            logger.error(f"ML service connection error: {str(e)}")
            return {"success": False, "message": "Connection error"}
    
    async def health_check(self) -> bool:
        """Проверка доступности ML сервиса"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except:
            return False



def generate_yandex_maps_url(from_coords: List[float], to_coords: List[float], to_name: str = "Место рыбалки") -> str:
    """Генерация ссылки на маршрут в Яндекс.Картах"""
    if not from_coords or not to_coords or len(from_coords) < 2 or len(to_coords) < 2:
        return None
    
    # Формат: https://yandex.ru/maps/?rtext=откуда~куда&rtt=auto
    from_str = f"{from_coords[0]},{from_coords[1]}"
    to_str = f"{to_coords[0]},{to_coords[1]}"
    
    url = f"https://yandex.ru/maps/?rtext={from_str}~{to_str}&rtt=auto"
    return url
