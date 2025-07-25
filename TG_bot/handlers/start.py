
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
from ML_integration import MLServiceClient, generate_yandex_maps_url
import os
from urllib.parse import quote
from database.requests import get_or_create_user, save_selected_spot, get_user_fishing_history

# ИМПОРТ КАЛЕНДАРЯ
from aiogram_calendar import SimpleCalendarCallback, SimpleCalendar
from datetime import datetime, date, timedelta

load_dotenv()
logger = logging.getLogger(__name__)

start_router = Router()

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL") 
ml_client = MLServiceClient(ML_SERVICE_URL)

class SearchStates(StatesGroup):
    waiting_for_search_request = State()
    browsing_spots = State()
    selecting_date = State()  # НОВОЕ СОСТОЯНИЕ ДЛЯ ВЫБОРА ДАТЫ

def get_spot_navigation_keyboard(current_index: int, total_spots: int, spot_id: str = None) -> InlineKeyboardMarkup:
    """Создает клавиатуру для навигации по местам"""
    buttons = []
    
    # Первая строка - навигация
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Предыдущее", 
            callback_data=f"spot_nav:prev:{current_index}"
        ))
    
    # Показываем текущую позицию
    nav_buttons.append(InlineKeyboardButton(
        text=f"{current_index + 1}/{total_spots}",
        callback_data="spot_info"
    ))
    
    if current_index < total_spots - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="Следующее ▶️", 
            callback_data=f"spot_nav:next:{current_index}"
        ))
    
    buttons.append(nav_buttons)
    
    # Вторая строка - действия
    action_buttons = []
    if spot_id:
        action_buttons.append(InlineKeyboardButton(
            text="✅ Выбрать это место", 
            callback_data=f"spot_select:{spot_id}:{current_index}"
        ))
    
    action_buttons.append(InlineKeyboardButton(
        text="🔄 Новый поиск", 
        callback_data="new_search"
    ))
    
    buttons.append(action_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def format_spot_description(spot: Dict, user_coords: List[float] = None) -> str:
    """Форматирует описание места для отображения"""
    text = f"🎣 <b>{spot['name']}</b>\n\n"
    
    # Координаты
    coordinates = spot.get('coordinates', [])
    if coordinates and len(coordinates) >= 2:
        lat, lon = coordinates[0], coordinates[1]
        text += f"📍 <b>Координаты:</b> {lat:.6f}, {lon:.6f}\n"
    
    # Расстояние
    if spot.get('distance_km') is not None:
        text += f"🚗 <b>Расстояние:</b> {spot['distance_km']:.1f} км\n"
    
    # Информация о рыбе и водоеме
    short_desc = spot.get('short_description', {})
    if isinstance(short_desc, dict):
        if short_desc.get('fish_types'):
            fish_list = ', '.join(short_desc['fish_types'])
            text += f"🐟 <b>Рыба:</b> {fish_list}\n"
        if short_desc.get('water_type'):
            text += f"🌊 <b>Тип водоема:</b> {short_desc['water_type']}\n"
    
    text += "\n"
    
    # Описание места
    description = spot.get('description', '')
    if description:
        text += f"📝 <b>Описание:</b>\n{description}\n\n"
    
    # Ссылка на маршрут
    if user_coords and coordinates:
        maps_url = generate_yandex_maps_url(user_coords, coordinates, spot['name'])
        if maps_url:
            text += f"🗺️ <a href='{maps_url}'>Построить маршрут в Яндекс.Картах</a>\n"
    
    return text

# Создаем клавиатуру для стартового меню
def get_start_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎣 Начать поиск мест")],
            [KeyboardButton(text="ℹ️ О нас")],
            [KeyboardButton(text="📚 История мест")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

@start_router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    await state.clear()  # Очищаем состояние при старте
    await message.answer(
        f"Привет, {message.from_user.first_name}! 🎣\n\n"
        "Добро пожаловать в FishAgent — ваш помощник в поиске идеальных мест для рыбалки!\n\n"
        "Выберите одну из опций:",
        reply_markup=get_start_keyboard()
    )

# Обработчик кнопки "О нас" - должен работать независимо от состояния
@start_router.message(F.text == "ℹ️ О нас")
async def about_us(message: Message, state: FSMContext):
    await state.clear()  # Очищаем состояние когда переходим к "О нас"
    await message.answer(
        "ℹ️ <b>О FishAgent</b>\n\n"
        "🎣 FishAgent — это интеллектуальный помощник для поиска интересных мест рыбалки.\n\n"
        "🤖 Мы используем машинное обучение для анализа ваших предпочтений и подбора наиболее подходящих водоемов.\n\n"
        "🌊 В нашей базе данных тысячи проверенных мест для рыбалки в Санкт-Петербурге.\n\n"
        "📱 Просто опишите, что вы ищете, и мы найдем лучшие варианты для вас!\n\n"
        "Разработано с ❤️ для рыбаков\n\n"
        "📢 Следите за обновлениями в "
        '<a href="https://t.me/fish_agent">нашем канале</a>!',
        parse_mode='HTML',
        reply_markup=get_start_keyboard()
    )

# Обработчик кнопки "Начать поиск мест" - должен работать независимо от состояния  
@start_router.message(F.text == "🎣 Начать поиск мест")
async def start_search(message: Message, state: FSMContext):
    try:
        await get_or_create_user(
            tg_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
    except Exception as e:
        logger.error(f"Ошибка создания или добавления пользователя в бд: {e}")
    await state.set_state(SearchStates.selecting_date)
    await message.answer(
        "📅 Пожалуйста, укажите дату вашей планируемой рыбалки. "
        "Это позволит нам подобрать лучшие места, предоставив информацию о том, "
        "сколько человек ожидается на месте в этот день."
    )
    # Показываем календарь
    calendar_markup = await SimpleCalendar().start_calendar()
    await message.answer("Выберите дату:", reply_markup=calendar_markup)
    await state.set_state(SearchStates.waiting_for_search_request)
    await message.answer(
        "🎣 <b>Поиск мест для рыбалки</b>\n\n"
        "Опишите ваши пожелания о рыбалке, включая:\n\n"
        "🐟 <b>Целевую рыбу</b> — какую рыбу хотите поймать\n"
        "📍 <b>Место отправления</b> — откуда планируете выезжать (необязательно, но поможет подобрать ближайшие места)\n"
        "🌊 <b>Тип водоема</b> — река, озеро, водохранилище или другое\n"
        "⏰ <b>Дополнительные пожелания</b> — условия ловли, пешком или на машине и т.д.\n\n"
        "<i>Пример: «Хочу поймать щуку, выезжаю от станции метро Автово, предпочитаю реки, планирую рыбалку на спиннинг»</i>\n\n"
        "Напишите ваш запрос:",
        parse_mode='HTML'
    )

@start_router.message(F.text == "📚 История мест")
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
        
        # Формируем текст истории
        history_text = "📚 <b>История ваших поездок</b>\n\n"
        
        for i, spot in enumerate(history, 1):
            # Форматируем дату
            date_str = spot.selected_at.strftime("%d.%m.%Y %H:%M")
            
            history_text += f"<b>{i}. {spot.spot_name}</b>\n"
            history_text += f"📅 {date_str}\n"
            
            # ПОКАЗЫВАЕМ ДАТУ РЫБАЛКИ ЕСЛИ ЕСТЬ
            if spot.fishing_date:
                fishing_date_str = spot.fishing_date.strftime("%d.%m.%Y")
                history_text += f"🎣 Дата рыбалки: <b>{fishing_date_str}</b>\n"
            
            if spot.user_query:
                # Обрезаем длинный запрос
                short_query = spot.user_query[:50] + "..." if len(spot.user_query) > 50 else spot.user_query
                history_text += f"🔍 Запрос: <i>{short_query}</i>\n"
            
            # Добавляем координаты если есть
            if spot.spot_coordinates:
                coords = spot.spot_coordinates.split(',')
                if len(coords) == 2:
                    history_text += f"🗺 <a href='https://yandex.ru/maps/?pt={coords[1]},{coords[0]}&z=15&l=map'>Показать на карте</a>\n"
            
            history_text += "\n"
        
        # Если история длинная, разбиваем на несколько сообщений
        if len(history_text) > 4000:
            # Разбиваем по записям
            parts = history_text.split('\n\n')
            current_part = "📚 <b>История ваших поездок</b>\n\n"
            
            for part in parts[1:]:  # Пропускаем заголовок
                if len(current_part + part + '\n\n') > 4000:
                    await message.answer(current_part, parse_mode='HTML')
                    current_part = part + '\n\n'
                else:
                    current_part += part + '\n\n'
            
            if current_part.strip():
                await message.answer(current_part, parse_mode='HTML')
        else:
            await message.answer(history_text, parse_mode='HTML')
        
        # Дополнительная информация
        await message.answer(
            f"Всего поездок: <b>{len(history)}</b>\n"
            f"Последняя поездка: <b>{history[0].selected_at.strftime('%d.%m.%Y')}</b>",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error showing history from menu: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке истории. Попробуйте позже.",
            parse_mode='HTML'
        )

# Обработчик текстовых сообщений ТОЛЬКО в состоянии ожидания поискового запроса
@start_router.message(SearchStates.waiting_for_search_request, F.text)
async def process_search_request(message: Message, state: FSMContext):
    user_request = message.text
    
    # Показываем, что обрабатываем запрос
    processing_msg = await message.answer("🔄 Анализируем ваш запрос и ищем подходящие места...")
    
    # Вызываем ML сервис для поиска мест
    result = await ml_client.search_fishing_spots(
        user_id=message.from_user.id,
        query=user_request
    )
    
    # Удаляем сообщение о обработке
    await processing_msg.delete()
    
    if result.get("success"):
        spots = result.get("spots", [])
        if spots:
            # Сохраняем результаты поиска в состояние
            user_coords = None
            if spots and spots[0].get("location_user"):
                user_coords = spots[0]["location_user"]
            
            await state.update_data(
                spots=spots,
                current_index=0,
                user_coordinates=user_coords,
                user_query=user_request
            )
            await state.set_state(SearchStates.browsing_spots)
            
            # Показываем первое место
            await show_spot(message, spots[0], 0, len(spots), user_coords, state)
        else:
            await message.answer(
                "😔 К сожалению, подходящие места не найдены. Попробуйте изменить запрос или добавить больше деталей.",
                reply_markup=get_start_keyboard()
            )
    else:
        error_msg = result.get("message", "Неизвестная ошибка")
        await message.answer(
            f"❌ Произошла ошибка при обработке запроса: {error_msg}\n\n"
            "Попробуйте позже или измените запрос.",
            reply_markup=get_start_keyboard()
        )
    
    if not result.get("success") or not result.get("spots"):
        await state.clear()

async def show_spot(message_or_callback, spot: dict, current_index: int, total_spots: int,
                    user_coords: list = None, state: FSMContext = None):
    """Отображает информацию о месте рыбалки с фото и кнопками навигации в одном сообщении"""
    try:
        # Определяем chat_id и объект бота
        if isinstance(message_or_callback, CallbackQuery):
            chat_id = message_or_callback.message.chat.id
            bot_instance = message_or_callback.bot
            user_id = message_or_callback.from_user.id
        else:  # Message
            chat_id = message_or_callback.chat.id
            bot_instance = message_or_callback.bot
            user_id = message_or_callback.from_user.id
        
        logger.info(f"Showing spot #{current_index+1}/{total_spots} for user {user_id}: {spot.get('name')}")

        # Формируем описание и клавиатуру
        description = format_spot_description(spot, user_coords)
        spot_id = spot.get('id', str(current_index))
        keyboard = get_spot_navigation_keyboard(current_index, total_spots, spot_id)
        
        # Получаем список фото или заглушки
        photos = spot.get('photos') or spot.get('images') or []
        logger.debug(f"Found {len(photos)} photos for spot")
        
        # Если нет фото - используем заглушку
        if not photos:
            logger.warning("No photos found, using fallback image")
            photos = [r"C:\Users\user\Desktop\projects\fishing_agent\TG_bot\4474172e-20de-4264-aafa-a94c66abd7b2.png", r"C:\Users\user\Desktop\projects\fishing_agent\TG_bot\ecaecf1e-ce43-4d72-9555-7b83d73dabe5.png", r"C:\Users\user\Desktop\projects\fishing_agent\TG_bot\i-_3_.png"]
        
        # Берем максимум 3 фото
        selected_photos = photos[:3]
        logger.debug(f"Selected {len(selected_photos)} photos for display")
        
        # Подготавливаем медиа-объекты
        media_items = []
        for idx, photo in enumerate(selected_photos):
            try:
                # Локальные файлы
                if isinstance(photo, str) and os.path.isfile(photo):
                    logger.debug(f"Using local file: {photo}")
                    media = InputMediaPhoto(media=FSInputFile(photo))
                
                # URL изображений
                elif isinstance(photo, str) and photo.startswith(('http://', 'https://')):
                    logger.debug(f"Using URL: {photo}")
                    media = InputMediaPhoto(media=photo)
                
                # Некорректный формат
                else:
                    logger.warning(f"Unsupported photo format: {type(photo)} - {str(photo)[:50]}")
                    continue
                
                # Первое фото с описанием
                if idx == 0:
                    media.caption = description
                    media.parse_mode = 'HTML'
                
                media_items.append(media)
            except Exception as e:
                logger.error(f"Error preparing media #{idx}: {str(e)}")
        
        # Если не удалось подготовить ни одного медиа-объекта
        if not media_items:
            logger.error("No valid media items prepared, using text fallback")
            # Создаем текстовое сообщение с клавиатурой
            text_message = f"⚠️ Ошибка загрузки фото. Показано текстовое описание:\n\n{description}"
            media_items = None
        else:
            text_message = None
        
        # Получаем данные состояния (если есть)
        state_data = await state.get_data() if state else {}
        last_message_ids = state_data.get('last_message_ids', [])
        
        # Удаляем предыдущие сообщения (если они есть)
        if last_message_ids:
            logger.debug(f"Deleting {len(last_message_ids)} previous messages")
            for msg_id in last_message_ids:
                try:
                    await bot_instance.delete_message(chat_id, msg_id)
                except Exception as e:
                    logger.warning(f"Error deleting message {msg_id}: {str(e)}")
        
        # Отправляем новые сообщения
        new_message_ids = []
        
        try:
            if media_items:
                # Отправляем медиагруппу
                logger.info(f"Sending media group with {len(media_items)} items")
                media_messages = await bot_instance.send_media_group(chat_id, media_items)
                new_message_ids = [msg.message_id for msg in media_messages]
                logger.info(f"Media group sent with IDs: {new_message_ids}")
                
                # Отправляем сообщение с клавиатурой
                keyboard_msg = await bot_instance.send_message(
                    chat_id, 
                    "Выберите действие:", 
                    reply_markup=keyboard
                )
                new_message_ids.append(keyboard_msg.message_id)
                logger.info(f"Keyboard message ID: {keyboard_msg.message_id}")
            
            else:
                # Отправляем текстовое сообщение с клавиатурой
                logger.warning("Sending text fallback message")
                fallback_msg = await bot_instance.send_message(
                    chat_id,
                    text_message,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                new_message_ids.append(fallback_msg.message_id)
            
            logger.info(f"Total new messages: {len(new_message_ids)}")
        
        except Exception as e:
            logger.error(f"Error sending messages: {str(e)}")
            
            # Фоллбэк: отправляем простой текст
            try:
                logger.error("Trying minimal text fallback")
                error_msg = await bot_instance.send_message(
                    chat_id,
                    "⚠️ Ошибка отображения места. Попробуйте выбрать другое место.",
                    reply_markup=keyboard
                )
                new_message_ids.append(error_msg.message_id)
            except Exception as ex:
                logger.critical(f"Complete fallback failure: {ex}")
        
        # Обновляем состояние новыми ID сообщений
        if state:
            await state.update_data(last_message_ids=new_message_ids)
    
    except Exception as e:
        logger.critical(f"Critical error in show_spot: {str(e)}")
        # В крайнем случае пытаемся отправить текстовое сообщение
        try:
            if isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.message.answer(
                    "⚠️ Произошла критическая ошибка при отображении места. Попробуйте начать поиск заново.",
                    reply_markup=get_start_keyboard()
                )
            else:
                await message_or_callback.answer(
                    "⚠️ Произошла критическая ошибка при отображении места. Попробуйте начать поиск заново.",
                    reply_markup=get_start_keyboard()
                )
        except:
            pass

# Обработчик callback'ов для навигации
@start_router.callback_query(F.data.startswith("spot_nav:"))
async def handle_spot_navigation(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    data = await state.get_data()
    spots = data.get('spots', [])
    user_coords = data.get('user_coordinates')
    
    if not spots:
        await callback.message.edit_text("❌ Данные поиска утеряны. Начните новый поиск.")
        await state.clear()
        return
    
    # Парсим callback data
    _, direction, current_index_str = callback.data.split(":")
    current_index = int(current_index_str)
    
    if direction == "prev" and current_index > 0:
        new_index = current_index - 1
    elif direction == "next" and current_index < len(spots) - 1:
        new_index = current_index + 1
    else:
        return  # Некорректная навигация
    
    # Обновляем индекс в состоянии
    await state.update_data(current_index=new_index)
    
    # Показываем новое место
    await show_spot(callback, spots[new_index], new_index, len(spots), user_coords, state)


@start_router.callback_query(F.data.startswith("spot_select:"))
async def handle_spot_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    spots = data.get('spots', [])
    user_query = data.get('user_query', '')
    user_coordinates = data.get('user_coordinates')
    fishing_date = data.get('fishing_date')  # получаем сохраненную дату

    # Парсим callback data
    _, spot_id, index_str = callback.data.split(":")
    index = int(index_str)

    if index < len(spots):
        selected_spot = spots[index]
        try:
            # Сохраняем выбранное место с датой в базу данных
            await save_selected_spot(
                tg_id=callback.from_user.id,
                spot_data=selected_spot,
                user_query=user_query,
                user_coordinates=user_coordinates,
                fishing_date=fishing_date  # передаем дату
            )
            logger.info(
                f"Saved selected spot for user {callback.from_user.id}: "
                f"{selected_spot.get('name')} on {fishing_date}"
            )
        except Exception as e:
            logger.error(f"Error saving selected spot: {e}")

        # Ответ пользователю и кнопки
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Новый поиск", callback_data="new_search")],
            [InlineKeyboardButton(text="📚 История мест", callback_data="show_history")]
        ])
        date_str = fishing_date.strftime('%d.%m.%Y') if fishing_date else 'не указана'
        await callback.message.edit_text(
            f"✅ <b>Место выбрано и сохранено!</b>\n\n"
            f"Вы выбрали: <b>{selected_spot['name']}</b>\n"
            f"📅 Дата: <b>{date_str}</b>\n\n"
            f"🎣 Удачной рыбалки!",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    await state.clear()


# ОБРАБОТЧИК КАЛЕНДАРЯ: сохраняем дату в состоянии, не пишем в БД
@start_router.callback_query(SimpleCalendarCallback.filter())
async def process_calendar_selection(callback: CallbackQuery,
                                     callback_data: SimpleCalendarCallback,
                                     state: FSMContext):
    """Обработчик выбора даты в календаре"""
    selected, selected_date = await SimpleCalendar().process_selection(callback, callback_data)
    if not selected:
        return

    # Нормализуем тип даты к datetime.date
    if isinstance(selected_date, datetime):
        selected_date = selected_date.date()

    # Проверяем, что дата не в прошлом
    if selected_date < date.today():
        await callback.answer("❌ Нельзя выбрать дату в прошлом!", show_alert=True)
        today = date.today()
        calendar_markup = await SimpleCalendar().start_calendar(year=today.year, month=today.month)
        try:
            await callback.message.edit_reply_markup(reply_markup=calendar_markup)
        except Exception as e:
            logger.warning(f"Ошибка при повторной отрисовке календаря: {e}")
        return

    # Сохраняем дату в состоянии
    await state.update_data(fishing_date=selected_date)
    await callback.answer(f"Дата выбрана: {selected_date.strftime('%d.%m.%Y')}")

    # Удаляем сообщение с календарем
    try:
        await callback.message.delete()
    except Exception:
        pass
    await state.set_state(SearchStates.waiting_for_search_request)
    await callback.message.answer(
        "🎣 <b>Поиск мест для рыбалки</b>\n\n"
        "Опишите ваши пожелания о рыбалке, включая:\n\n"
        "🐟 <b>Целевую рыбу</b> — какую рыбу хотите поймать\n"
        "📍 <b>Место отправления</b> — откуда планируете выезжать (необязательно, но поможет подобрать ближайшие места)\n"
        "🌊 <b>Тип водоема</b> — река, озеро, водохранилище или другое\n"
        "⏰ <b>Дополнительные пожелания</b> — условия ловли, пешком или на машине и т.д.\n\n"
        "<i>Пример: «Хочу поймать щуку, выезжаю от станции метро Автово, предпочитаю реки, планирую рыбалку на спиннинг»</i>\n\n"
        "Напишите ваш запрос:",
        parse_mode='HTML'
    )

# НОВЫЙ ОБРАБОТЧИК ДЛЯ ПОКАЗА ИСТОРИИ ИЗ INLINE КНОПКИ
@start_router.callback_query(F.data == "show_history")
async def handle_show_history_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик inline кнопки 'Моя история'"""
    await callback.answer()
    
    try:
        history = await get_user_fishing_history(callback.from_user.id, limit=10)
        
        if not history:
            await callback.message.edit_text(
                "📚 <b>История ваших поездок</b>\n\n"
                "У вас пока нет сохраненных мест для рыбалки.\n"
                "Начните поиск, чтобы выбрать первое место!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎣 Начать поиск", callback_data="start_search")]
                ])
            )
            return
        
        # Формируем текст истории (сокращенный для inline)
        history_text = "📚 <b>Последние поездки</b>\n\n"
        
        for i, spot in enumerate(history[:5], 1):  # Показываем только 5 последних
            date_str = spot.selected_at.strftime("%d.%m")
            history_text += f"<b>{i}. {spot.spot_name}</b>\n"
            
            if spot.fishing_date:
                fishing_date_str = spot.fishing_date.strftime("%d.%m.%Y")
                history_text += f"🎣 {fishing_date_str}\n"
            else:
                history_text += f"📅 {date_str}\n"
            
            history_text += "\n"
        
        if len(history) > 5:
            history_text += f"И еще {len(history) - 5} поездок...\n\n"
        
        history_text += "Полную историю смотрите в главном меню бота."
        
        await callback.message.edit_text(
            history_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎣 Новый поиск", callback_data="start_search")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Error showing history from callback: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке истории.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="show_history")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )

# Обработчик нового поиска
@start_router.callback_query(F.data == "new_search")
async def handle_new_search(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        "🎣 Начните новый поиск!\n\nВыберите одну из опций:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎣 Начать поиск мест", callback_data="start_search")],
            [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about_us")]
        ])
    )

@start_router.callback_query(F.data == "start_search")
async def handle_start_search_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()  # Подтверждаем получение callback
    
    # Устанавливаем состояние выбора даты
    await state.set_state(SearchStates.selecting_date)
    
    # Отправляем сообщение с объяснением
    await callback.message.answer(
        "📅 Пожалуйста, укажите дату вашей планируемой рыбалки. "
        "Это позволит нам подобрать лучшие места, предоставив информацию о том, "
        "сколько человек ожидается на месте в этот день."
    )
    
    # Показываем календарь в новом сообщении
    calendar_markup = await SimpleCalendar().start_calendar()
    await callback.message.answer("Выберите дату:", reply_markup=calendar_markup)

@start_router.callback_query(F.data == "about_us")
async def handle_about_us_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()  # Очищаем состояние при переходе к "О нас"
    
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
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎣 Начать поиск мест", callback_data="start_search")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
    )

@start_router.callback_query(F.data == "main_menu")
async def handle_main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        "🏠 Главное меню\n\nВыберите одну из опций:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎣 Начать поиск мест", callback_data="start_search")],
            [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about_us")]
        ])
    )

# Обработчик для возврата в главное меню
@start_router.message(F.text.in_(["🏠 Главное меню", "/menu"]))
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 Главное меню\n\nВыберите одну из опций:",
        reply_markup=get_start_keyboard()
    )

# Обработчик для игнорирования callback'а с информацией о позиции
@start_router.callback_query(F.data == "spot_info")
async def handle_spot_info(callback: CallbackQuery):
    await callback.answer("ℹ️ Текущая позиция в результатах поиска", show_alert=True)

# Обработчик для всех остальных текстовых сообщений (когда не в состоянии поиска)
@start_router.message(F.text)
async def handle_other_text(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    # Если пользователь не в состоянии поиска, предлагаем начать поиск
    if current_state != SearchStates.waiting_for_search_request:
        await message.answer(
            "🤔 Я не понял ваше сообщение.\n\n"
            "Для поиска мест рыбалки нажмите кнопку «🎣 Начать поиск мест», "
            "а для информации о боте — «ℹ️ О нас».",
            reply_markup=get_start_keyboard()
        )


