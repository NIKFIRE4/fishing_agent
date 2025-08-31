import os
import logging
from typing import List
from aiogram.types import InputMediaPhoto, FSInputFile

logger = logging.getLogger(__name__)

class MediaHandler:
    FALLBACK_PHOTOS = [
        r"C:\Users\user\Desktop\projects\fishing_agent\TG_bot\4474172e-20de-4264-aafa-a94c66abd7b2.png",
        r"C:\Users\user\Desktop\projects\fishing_agent\TG_bot\ecaecf1e-ce43-4d72-9555-7b83d73dabe5.png", 
        r"C:\Users\user\Desktop\projects\fishing_agent\TG_bot\i-_3_.png"
    ]
    
    @staticmethod
    def prepare_media_items(photos: List, description: str, max_photos: int = 3) -> List[InputMediaPhoto]:
        """Подготавливает медиа-объекты для отправки"""
        if not photos:
            photos = MediaHandler.FALLBACK_PHOTOS
        
        selected_photos = photos[:max_photos]
        media_items = []
        
        for idx, photo in enumerate(selected_photos):
            try:
                if isinstance(photo, str) and os.path.isfile(photo):
                    media = InputMediaPhoto(media=FSInputFile(photo))
                elif isinstance(photo, str) and photo.startswith(('http://', 'https://')):
                    media = InputMediaPhoto(media=photo)
                else:
                    continue
                
                if idx == 0:
                    media.caption = description
                    media.parse_mode = 'HTML'
                
                media_items.append(media)
            except Exception as e:
                logger.error(f"Error preparing media #{idx}: {str(e)}")
        
        return media_items