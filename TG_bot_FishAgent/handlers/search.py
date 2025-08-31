import os
from dotenv import load_dotenv
import whisper
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram_calendar import SimpleCalendarCallback, SimpleCalendar
from datetime import datetime, date
import logging
from aiogram_calendar.schemas import CalendarLabels
import calendar

from config.settings import MESSAGES, ML_SERVICE_URL
from states.search_states import SearchStates
from keyboards.main_menu import get_start_keyboard
from handlers.navigation import show_spot
from database.requests import get_or_create_user
from ML_integration import MLServiceClient
from utils.voice_processor import process_voice_message, is_voice_available

logger = logging.getLogger(__name__)
search_router = Router()

try:
    logger.info("Загрузка модели Whisper...")
    whisper_model = whisper.load_model("small")  # Можно изменить на "base" или "tiny"
    logger.info("Модель Whisper загружена успешно")
except Exception as e:
    logger.error(f"Ошибка загрузки модели Whisper: {e}")
    whisper_model = None

class RussianCalendar(SimpleCalendar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Прямо заменяем подписи:
        self._labels = CalendarLabels(
            cancel_caption="Отмена",
            today_caption="Сегодня",
            days_of_week=["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
            months=[
                "Январь", "Февраль", "Март", "Апрель",
                "Май", "Июнь", "Июль", "Август",
                "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
            ],
        )

@search_router.message(F.text == "🎣 Начать поиск мест")
async def start_search(message: Message, state: FSMContext):
    """
    Начало поиска: сохраняем пользователя, запрашиваем дату через календарь и показываем подсказку из MESSAGES.
    """
    try:
        await get_or_create_user(
            tg_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
    except Exception as e:
        logger.error(f"Ошибка создания пользователя: {e}")

    # Переключаем состояние на выбор даты
    await state.set_state(SearchStates.selecting_date)
    await message.answer(
        MESSAGES['search']['date_prompt'],
        parse_mode='HTML'
    )

    # Отправляем календарь
    calendar_markup = await RussianCalendar().start_calendar()
    await message.answer(
        "Выберите дату:",
        reply_markup=calendar_markup
    )

@search_router.callback_query(SimpleCalendarCallback.filter())
async def process_calendar_selection(callback: CallbackQuery,
                                     callback_data: SimpleCalendarCallback,
                                     state: FSMContext):
    """
    Обработка выбора даты. Проверяем на прошлую дату, сохраняем в FSM и запрашиваем текстовый запрос.
    """
    # Специальная обработка кнопки "Сегодня"
    if str(callback_data.act) == "SimpleCalAct.today":
        selected_date = date.today()
        selected = True
    else:
        selected, selected_date = await RussianCalendar().process_selection(callback, callback_data)
        
        # Если календарь еще не завершил выбор (пользователь переключает месяцы/годы)
        if not selected:
            return

    # Приводим к типу date, если получили datetime
    if isinstance(selected_date, datetime):
        selected_date = selected_date.date()

    # Проверяем, что дата не в прошлом
    if selected_date < date.today():
        await callback.answer(
            MESSAGES['search']['past_date_error'], show_alert=True
        )
        # Перерисовываем календарь на текущий месяц
        today = date.today()
        calendar_markup = await RussianCalendar().start_calendar(year=today.year, month=today.month)
        try:
            await callback.message.edit_reply_markup(reply_markup=calendar_markup)
        except Exception as e:
            logger.warning(f"Ошибка при перерисовке календаря: {e}")
        return

    # Сохраняем дату в состоянии пользователя
    await state.update_data(fishing_date=selected_date)
    await callback.answer(
        MESSAGES['search']['date_selected'].format(
            date=selected_date.strftime('%d.%m.%Y')
        )
    )

    # Удаляем старое сообщение с календарем
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Переходим к вводу поискового запроса
    await state.set_state(SearchStates.waiting_for_search_request)
    request_message = MESSAGES['search']['request_prompt']
    if is_voice_available():
        request_message += "\n\n🎤 <i>Вы можете отправить текст или записать голосовое сообщение</i>"
    
    await callback.message.answer(
        request_message,
        parse_mode='HTML'
    )

async def process_search_query(message: Message, state: FSMContext, user_request: str, processing_msg: Message):
    """
    Общая функция для обработки поискового запроса (текстового или голосового).
    """
    try:
        ml_client = MLServiceClient(ML_SERVICE_URL)
        result = await ml_client.search_fishing_spots(
            user_id=message.from_user.id,
            query=user_request
        )

        await processing_msg.delete()

        if result.get("success"):
            spots = result.get("spots", [])
            if spots:
                user_coords = spots[0].get("location_user")
                # Сохраняем результаты и текущий индекс
                await state.update_data(
                    spots=spots,
                    current_index=0,
                    user_coordinates=user_coords,
                    user_query=user_request
                )
                await state.set_state(SearchStates.browsing_spots)
                data = await state.get_data()
                selected_date = data.get("fishing_date")
                # Показываем первую локацию
                await show_spot(
                    message, spots[0], 0, len(spots), user_coords, state, selected_date
                )
            else:
                await message.answer(
                    MESSAGES['search']['no_results'],
                    reply_markup=get_start_keyboard()
                )
                await state.clear()
        else:
            error_msg = result.get("message", "Неизвестная ошибка")
            await message.answer(
                MESSAGES['search']['error'].format(error=error_msg),
                reply_markup=get_start_keyboard()
            )
            await state.clear()
    
    except Exception as e:
        logger.error(f"Ошибка при обработке поискового запроса: {e}")
        try:
            await processing_msg.delete()
        except:
            pass
        await message.answer(
            "❌ Произошла ошибка при обработке запроса. Попробуйте еще раз.",
            reply_markup=get_start_keyboard()
        )
        await state.clear()

# ДОБАВЛЕН ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ
@search_router.message(SearchStates.waiting_for_search_request, F.text)
async def process_text_search_request(message: Message, state: FSMContext):
    """
    Обработка текстового сообщения пользователя для поискового запроса.
    """
    user_request = message.text.strip()
    
    if not user_request:
        await message.answer("Пожалуйста, введите ваш запрос для поиска мест рыбалки.")
        return
    
    # Показываем индикатор обработки
    processing_msg = await message.answer("🔍 Ищу места для рыбалки...")
    
    # Обрабатываем запрос
    await process_search_query(message, state, user_request, processing_msg)

@search_router.message(SearchStates.waiting_for_search_request, F.voice)
async def process_voice_search_request(message: Message, state: FSMContext):
    """
    Обработка голосового сообщения пользователя для поискового запроса.
    """
    # Показываем индикатор обработки
    processing_msg = await message.answer("🎤 Распознаю речь...")

    try:
        # Используем наш модуль для обработки голоса, передаем bot
        result = await process_voice_message(message.voice, message.bot)
        
        if result["success"]:
            user_request = result["text"]
            
            # Показываем распознанный текст пользователю
            await processing_msg.edit_text(
                f"✅ Распознано: <i>«{user_request}»</i>\n\n🔍 Ищу места для рыбалки...", 
                parse_mode='HTML'
            )
            
            # Обрабатываем запрос
            await process_search_query(message, state, user_request, processing_msg)
        else:
            # Показываем ошибку
            await processing_msg.edit_text(
                f"❌ {result['error']}. Попробуйте еще раз или отправьте текстовое сообщение."
            )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке голосового сообщения: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка при распознавании речи. Попробуйте отправить текстовое сообщение."
        )

@search_router.message(F.voice)
async def handle_unexpected_voice(message: Message, state: FSMContext):
    """
    Обработка голосовых сообщений в неожиданных состояниях.
    """
    current_state = await state.get_state()
    if current_state != SearchStates.waiting_for_search_request:
        voice_hint = " с голосовыми сообщениями" if is_voice_available() else ""
        await message.answer(
            f"🎤 Поиск{voice_hint} возможен только после выбора даты.\n"
            "Нажмите «🎣 Начать поиск мест» для начала поиска."
        )