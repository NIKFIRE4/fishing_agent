from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from database.requests import get_user_fishing_history
from keyboards.inline import get_history_keyboard
from utils.formatters import format_history_text

logger = logging.getLogger(__name__)
history_router = Router()

@history_router.message(F.text == "📚 История мест")
async def show_history_from_menu(message: Message):
    """Обработчик кнопки 'История мест' из главного меню"""
    try:
        history = await get_user_fishing_history(message.from_user.id, limit=10)
        
        if not history:
            await message.answer(
                "📚 <b>История ваших поездок</b>\n\n"
                "У вас пока нет сохраненных мест для рыбалки.\n"
                "Начните поиск, чтобы выбрать первое место!",
                parse_mode='HTML'
            )
            return
        
        # Подробная история для главного меню
        history_text = "📚 <b>История ваших поездок</b>\n\n"
        
        for i, spot in enumerate(history, 1):
            date_str = spot.selected_at.strftime("%d.%m.%Y %H:%M")
            history_text += f"<b>{i}. {spot.spot_name}</b>\n"
            history_text += f"📅 {date_str}\n"
            
            if spot.fishing_date:
                fishing_date_str = spot.fishing_date.strftime("%d.%m.%Y")
                history_text += f"🎣 Дата рыбалки: <b>{fishing_date_str}</b>\n"
            
            if spot.user_query:
                short_query = spot.user_query[:50] + "..." if len(spot.user_query) > 50 else spot.user_query
                history_text += f"🔍 Запрос: <i>{short_query}</i>\n"
            
            if spot.spot_coordinates:
                coords = spot.spot_coordinates.split(',')
                if len(coords) == 2:
                    history_text += f"🗺 <a href='https://yandex.ru/maps/?pt={coords[1]},{coords[0]}&z=15&l=map'>Показать на карте</a>\n"
            
            history_text += "\n"
        
        await message.answer(history_text, parse_mode='HTML')
        
        await message.answer(
            f"Всего поездок: <b>{len(history)}</b>\n"
            f"Последняя поездка: <b>{history[0].selected_at.strftime('%d.%m.%Y')}</b>",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error showing history: {e}")
        await message.answer("❌ Произошла ошибка при загрузке истории.")

@history_router.callback_query(F.data == "show_history")
async def handle_show_history_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик inline кнопки 'История'"""
    await callback.answer()
    
    try:
        history = await get_user_fishing_history(callback.from_user.id, limit=10)
        history_text = format_history_text(history, limit=5)
        
        if history and len(history) > 5:
            history_text += "Полную историю смотрите в главном меню бота."
        
        await callback.message.edit_text(
            history_text,
            parse_mode='HTML',
            reply_markup=get_history_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error showing history from callback: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке истории.",
            reply_markup=get_history_keyboard()
        )