from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram_calendar import SimpleCalendar
import logging

from keyboards.inline import get_main_menu_inline_keyboard
from keyboards.main_menu import get_start_keyboard
from database.requests import save_selected_spot

logger = logging.getLogger(__name__)
callbacks_router = Router()

@callbacks_router.callback_query(F.data.startswith("spot_select:"))
async def handle_spot_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    spots = data.get('spots', [])
    user_query = data.get('user_query', '')
    user_coordinates = data.get('user_coordinates')
    fishing_date = data.get('fishing_date')

    _, spot_id, index_str = callback.data.split(":")
    index = int(index_str)

    if index < len(spots):
        selected_spot = spots[index]
        try:
            await save_selected_spot(
                tg_id=callback.from_user.id,
                spot_data=selected_spot,
                user_query=user_query,
                user_coordinates=user_coordinates,
                fishing_date=fishing_date
            )
        except Exception as e:
            logger.error(f"Error saving selected spot: {e}")

        from keyboards.inline import get_history_keyboard
        date_str = fishing_date.strftime('%d.%m.%Y') if fishing_date else 'не указана'
        await callback.message.edit_text(
            f"✅ <b>Место выбрано и сохранено!</b>\n\n"
            f"Вы выбрали: <b>{selected_spot['name']}</b>\n"
            f"📅 Дата: <b>{date_str}</b>\n\n"
            f"🎣 Удачной рыбалки!",
            parse_mode='HTML',
            reply_markup=get_history_keyboard()
        )
    await state.clear()

@callbacks_router.callback_query(F.data == "new_search")
async def handle_new_search(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        "🎣 Начните новый поиск!\n\nВыберите одну из опций:",
        reply_markup=get_main_menu_inline_keyboard()
    )

@callbacks_router.callback_query(F.data == "start_search")
async def handle_start_search_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    from states.search_states import SearchStates
    await state.set_state(SearchStates.selecting_date)
    
    await callback.message.answer(
        "📅 Пожалуйста, укажите дату вашей планируемой рыбалки. "
        "Это позволит нам подобрать лучшие места, предоставив информацию о том, "
        "сколько человек ожидается на месте в этот день."
    )
    
    calendar_markup = await SimpleCalendar().start_calendar()
    await callback.message.answer("Выберите дату:", reply_markup=calendar_markup)

@callbacks_router.callback_query(F.data == "about_us")
async def handle_about_us_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        "ℹ️ <b>О FishAgent</b>\n\n"
        "🎣 FishAgent — это интеллектуальный помощник для поиска интересных мест рыбалки.\n\n"
        "🤖 Мы используем машинное обучение для анализа ваших предпочтений и подбора наиболее подходящих водоемов.\n\n"
        "🌊 В нашей базе данных тысячи проверенных мест для рыбалки в Санкт-Петербурге.\n\n"
        "📱 Просто опишите, что вы ищете, и мы найдем лучшие варианты для вас!\n\n"
        "Разработано с ❤️ для рыбаков\n\n"
        "📢 Следите за обновлениями в "
        '<a href="https://t.me/fish_agent">нашем канале</a>!\n\n'
        "Выберите одну из опций:",
        parse_mode='HTML',
        reply_markup=get_main_menu_inline_keyboard()
    )

@callbacks_router.callback_query(F.data == "main_menu")
async def handle_main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        "🏠 Главное меню\n\nВыберите одну из опций:",
        reply_markup=get_main_menu_inline_keyboard()
    )