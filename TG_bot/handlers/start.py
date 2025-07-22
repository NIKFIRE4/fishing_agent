from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp
import asyncio
from dotenv import load_dotenv
from typing import Optional, List, Dict
import logging
import os
from urllib.parse import quote

load_dotenv()
logger = logging.getLogger(__name__)

start_router = Router()

class SearchStates(StatesGroup):
    waiting_for_search_request = State()
    browsing_spots = State()

# Конфигурация ML сервиса
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL") 

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

# Инициализация клиента ML сервиса
ml_client = MLServiceClient(ML_SERVICE_URL)

def generate_yandex_maps_url(from_coords: List[float], to_coords: List[float], to_name: str = "Место рыбалки") -> str:
    """Генерация ссылки на маршрут в Яндекс.Картах"""
    if not from_coords or not to_coords or len(from_coords) < 2 or len(to_coords) < 2:
        return None
    
    # Формат: https://yandex.ru/maps/?rtext=откуда~куда&rtt=auto
    from_str = f"{from_coords[0]},{from_coords[1]}"
    to_str = f"{to_coords[0]},{to_coords[1]}"
    
    url = f"https://yandex.ru/maps/?rtext={from_str}~{to_str}&rtt=auto"
    return url

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
            [KeyboardButton(text="ℹ️ О нас")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

@start_router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 🎣\n\n"
        "Добро пожаловать в FishAgent — ваш помощник в поиске идеальных мест для рыбалки!\n\n"
        "Выберите одну из опций:",
        reply_markup=get_start_keyboard()
    )

@start_router.message(F.text == "🎣 Начать поиск мест")
async def start_search(message: Message, state: FSMContext):
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

@start_router.message(SearchStates.waiting_for_search_request)
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
                user_coordinates=user_coords
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

async def show_spot(message_or_callback, spot: Dict, current_index: int, total_spots: int, user_coords: List[float] = None, state: FSMContext = None):
    """Отображает информацию о конкретном месте рыбалки"""
    
    # Формируем описание места
    description = format_spot_description(spot, user_coords)
    
    # Создаем клавиатуру навигации
    spot_id = spot.get('id', str(current_index))
    keyboard = get_spot_navigation_keyboard(current_index, total_spots, spot_id)
    
    # Получаем фотографии места (если есть)
    photos = spot.get('photos', [])
    
    try:
        if isinstance(message_or_callback, CallbackQuery):
            # Это callback от кнопки
            callback = message_or_callback
            
            if photos:
                # Если есть фото, отправляем медиа-группу
                if len(photos) == 1:
                    await callback.message.edit_media(
                        media=InputMediaPhoto(media=photos[0], caption=description, parse_mode='HTML'),
                        reply_markup=keyboard
                    )
                else:
                    # Для множественных фото - удаляем старое сообщение и отправляем новое
                    await callback.message.delete()
                    media_group = [InputMediaPhoto(media=photos[0], caption=description, parse_mode='HTML')]
                    for photo in photos[1:]:
                        media_group.append(InputMediaPhoto(media=photo))
                    
                    messages = await callback.message.answer_media_group(media_group)
                    # Отправляем клавиатуру отдельным сообщением
                    await callback.message.answer("Выберите действие:", reply_markup=keyboard)
            else:
                # Без фото - просто текст
                await callback.message.edit_text(
                    text=description,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
        else:
            # Это обычное сообщение
            message = message_or_callback
            
            if photos:
                if len(photos) == 1:
                    await message.answer_photo(
                        photo=photos[0],
                        caption=description,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
                else:
                    # Отправляем медиа-группу
                    media_group = [InputMediaPhoto(media=photos[0], caption=description, parse_mode='HTML')]
                    for photo in photos[1:]:
                        media_group.append(InputMediaPhoto(media=photo))
                    
                    await message.answer_media_group(media_group)
                    # Отправляем клавиатуру отдельным сообщением
                    await message.answer("Выберите действие:", reply_markup=keyboard)
            else:
                # Без фото - просто текст
                await message.answer(
                    text=description,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
    except Exception as e:
        logger.error(f"Error showing spot: {e}")
        # Fallback - отправляем простое текстовое сообщение
        await message_or_callback.message.answer(
            text=description,
            parse_mode='HTML',
            reply_markup=keyboard
        )

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

# Обработчик выбора места
@start_router.callback_query(F.data.startswith("spot_select:"))
async def handle_spot_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    data = await state.get_data()
    spots = data.get('spots', [])
    
    # Парсим callback data
    _, spot_id, index_str = callback.data.split(":")
    index = int(index_str)
    
    if index < len(spots):
        selected_spot = spots[index]
        
        await callback.message.edit_text(
            f"✅ <b>Место выбрано!</b>\n\n"
            f"Вы выбрали: <b>{selected_spot['name']}</b>\n\n"
            f"🎣 Удачной рыбалки! \n\n"
            f"Чтобы начать новый поиск, используйте кнопку ниже.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Новый поиск", callback_data="new_search")]
            ])
        )
    
    await state.clear()

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
    await callback.answer()
    
    await state.set_state(SearchStates.waiting_for_search_request)
    await callback.message.edit_text(
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

@start_router.message(F.text == "ℹ️ О нас")
async def about_us(message: Message):
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

@start_router.callback_query(F.data == "about_us")
async def handle_about_us_callback(callback: CallbackQuery):
    await callback.answer()
    
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