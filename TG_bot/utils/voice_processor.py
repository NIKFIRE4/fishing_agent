"""
Модуль для обработки голосовых сообщений с помощью Whisper
"""

import os
import asyncio
import tempfile
import logging
from typing import Optional
import whisper
from aiogram.types import Voice

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Класс для обработки голосовых сообщений"""
    
    def __init__(self, model_size: str = "large"):
        """
        Инициализация процессора голоса
        
        Args:
            model_size: Размер модели Whisper ("tiny", "base", "small", "medium", "large")
        """
        self.model = None
        self.model_size = model_size
        self._load_model()
    
    def _load_model(self):
        """Загрузка модели Whisper"""
        try:
            logger.info(f"Загрузка модели Whisper размера '{self.model_size}'...")
            self.model = whisper.load_model(self.model_size)
            logger.info("Модель Whisper загружена успешно")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели Whisper: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Проверка доступности модели"""
        return self.model is not None
    
    async def transcribe_voice_message(self, voice: Voice, bot) -> Optional[str]:
        """
        Распознавание голосового сообщения из Telegram
        
        Args:
            voice: Объект голосового сообщения из aiogram
            bot: Экземпляр бота для получения файла
            
        Returns:
            Распознанный текст или None в случае ошибки
        """
        if not self.is_available():
            raise Exception("Модель Whisper не загружена")
        
        try:
            # Получаем файл голосового сообщения через bot
            voice_file = await bot.get_file(voice.file_id)
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
                temp_path = temp_file.name
                await bot.download_file(voice_file.file_path, temp_path)
            
            # Распознаем речь
            text = await self._transcribe_audio_file(temp_path)
            
            # Удаляем временный файл
            os.unlink(temp_path)
            
            return text.strip() if text else None
            
        except Exception as e:
            logger.error(f"Ошибка при обработке голосового сообщения: {e}")
            raise
    
    async def _transcribe_audio_file(self, audio_path: str) -> str:
        """
        Асинхронное распознавание аудиофайла
        
        Args:
            audio_path: Путь к аудиофайлу
            
        Returns:
            Распознанный текст
        """
        try:
            # Выполняем в отдельном потоке, чтобы не блокировать бота
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._transcribe_sync, 
                audio_path
            )
            return result
        except Exception as e:
            logger.error(f"Ошибка при распознавании аудиофайла {audio_path}: {e}")
            raise
    
    def _transcribe_sync(self, audio_path: str) -> str:
        """
        Синхронное распознавание речи
        
        Args:
            audio_path: Путь к аудиофайлу
            
        Returns:
            Распознанный текст
        """
        try:
            # Распознаем с указанием языка
            result = self.model.transcribe(audio_path, language="ru")
            return result["text"]
        except Exception as e:
            logger.error(f"Ошибка при синхронном распознавании: {e}")
            return ""
    
    def reload_model(self, model_size: str = None):
        """
        Перезагрузка модели с возможностью смены размера
        
        Args:
            model_size: Новый размер модели (если не указан, используется текущий)
        """
        if model_size:
            self.model_size = model_size
        
        logger.info(f"Перезагрузка модели Whisper размера '{self.model_size}'...")
        self._load_model()


# Глобальный экземпляр процессора голоса
voice_processor = VoiceProcessor(model_size="large")


async def process_voice_message(voice: Voice, bot) -> dict:
    """
    Удобная функция для обработки голосового сообщения
    
    Args:
        voice: Объект голосового сообщения из aiogram
        bot: Экземпляр бота для получения файла
        
    Returns:
        Словарь с результатом: {"success": bool, "text": str, "error": str}
    """
    try:
        if not voice_processor.is_available():
            return {
                "success": False,
                "text": "",
                "error": "Распознавание голоса временно недоступно"
            }
        
        text = await voice_processor.transcribe_voice_message(voice, bot)
        
        if text:
            return {
                "success": True,
                "text": text,
                "error": ""
            }
        else:
            return {
                "success": False,
                "text": "",
                "error": "Не удалось распознать речь"
            }
            
    except Exception as e:
        logger.error(f"Ошибка в process_voice_message: {e}")
        return {
            "success": False,
            "text": "",
            "error": "Произошла ошибка при распознавании речи"
        }


def get_voice_processor() -> VoiceProcessor:
    """Получить экземпляр процессора голоса"""
    return voice_processor


def is_voice_available() -> bool:
    """Проверить доступность распознавания голоса"""
    return voice_processor.is_available()