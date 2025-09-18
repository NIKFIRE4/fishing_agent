from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from datetime import datetime, date
from keyboards.inline import get_spot_navigation_keyboard
from utils.formatters import format_spot_description
from utils.media_handler import MediaHandler

logger = logging.getLogger(__name__)
navigation_router = Router()

async def show_spot(message_or_callback, spot: dict, current_index: int, total_spots: int,
                    user_coords: list = None, state: FSMContext = None, selected_date: date = None):
    """Отображает информацию о месте рыбалки"""
    try:
        if hasattr(message_or_callback, 'message'):  # CallbackQuery
            chat_id = message_or_callback.message.chat.id
            bot_instance = message_or_callback.bot
            user_id = message_or_callback.from_user.id
        else:  # Message
            chat_id = message_or_callback.chat.id
            bot_instance = message_or_callback.bot
            user_id = message_or_callback.from_user.id
        
        description = await format_spot_description(spot, user_coords, selected_date)
        spot_id = spot.get('id', str(current_index))
        keyboard = get_spot_navigation_keyboard(current_index, total_spots, spot_id)
        
        photos = spot.get('photos') or spot.get('images') or []
        photos = [
                                r"C:\Users\user\Desktop\projects\fishing_agent\TG_bot_FishAgent\two.jpg",
                                r"C:\Users\user\Desktop\projects\fishing_agent\TG_bot_FishAgent\first.jpg",
                                r"C:\Users\user\Desktop\projects\fishing_agent\TG_bot_FishAgent\free.jpg"
                            ]
        media_items = MediaHandler.prepare_media_items(photos, description)
        
        # Получаем данные состояния
        state_data = await state.get_data() if state else {}
        last_message_ids = state_data.get('last_message_ids', [])
        
        # Удаляем предыдущие сообщения
        for msg_id in last_message_ids:
            try:
                await bot_instance.delete_message(chat_id, msg_id)
            except Exception:
                pass
        
        new_message_ids = []
        
        if media_items:
            media_messages = await bot_instance.send_media_group(chat_id, media_items)
            new_message_ids = [msg.message_id for msg in media_messages]
            
            keyboard_msg = await bot_instance.send_message(
                chat_id, 
                "Выберите действие:", 
                reply_markup=keyboard
            )
            new_message_ids.append(keyboard_msg.message_id)
        else:
            fallback_msg = await bot_instance.send_message(
                chat_id,
                f"⚠️ Ошибка загрузки фото. Показано текстовое описание:\n\n{description}",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            new_message_ids.append(fallback_msg.message_id)
        
        if state:
            await state.update_data(last_message_ids=new_message_ids)
    
    except Exception as e:
        logger.error(f"Error in show_spot: {str(e)}")

@navigation_router.callback_query(F.data.startswith("spot_nav:"))
async def handle_spot_navigation(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    data = await state.get_data()
    selected_date = data.get("fishing_date")
    spots = data.get('spots', [])
    user_coords = data.get('user_coordinates')
    
    if not spots:
        await callback.message.edit_text("❌ Данные поиска утеряны. Начните новый поиск.")
        await state.clear()
        return
    
    _, direction, current_index_str = callback.data.split(":")
    current_index = int(current_index_str)
    
    if direction == "prev" and current_index > 0:
        new_index = current_index - 1
    elif direction == "next" and current_index < len(spots) - 1:
        new_index = current_index + 1
    else:
        return
    
    await state.update_data(current_index=new_index)
    await show_spot(callback, spots[new_index], new_index, len(spots), user_coords, state, selected_date)

@navigation_router.callback_query(F.data == "spot_info")
async def handle_spot_info(callback: CallbackQuery):
    await callback.answer("ℹ️ Текущая позиция в результатах поиска", show_alert=True)