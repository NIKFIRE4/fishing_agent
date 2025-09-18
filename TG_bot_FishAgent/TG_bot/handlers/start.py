from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.main_menu import get_start_keyboard
from database.requests import get_or_create_user
import logging

logger = logging.getLogger(__name__)
start_router = Router()

@start_router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привет, {message.from_user.first_name}! 🎣\n\n"
        "Добро пожаловать в FishAgent — ваш помощник в поиске идеальных мест для рыбалки!\n\n"
        "Выберите одну из опций:",
        reply_markup=get_start_keyboard()
    )

@start_router.message(F.text == "ℹ️ О нас")
async def about_us(message: Message, state: FSMContext):
    await state.clear()
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

@start_router.message(F.text.in_(["🏠 Главное меню", "/menu"]))
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 Главное меню\n\nВыберите одну из опций:",
        reply_markup=get_start_keyboard()
    )

@start_router.message(F.text)
async def handle_other_text(message: Message, state: FSMContext):
    from states.search_states import SearchStates
    
    current_state = await state.get_state()
    
    if current_state != SearchStates.waiting_for_search_request:
        await message.answer(
            "🤔 Я не понял ваше сообщение.\n\n"
            "Для поиска мест рыбалки нажмите кнопку «🎣 Начать поиск мест», "
            "а для информации о боте — «ℹ️ О нас».",
            reply_markup=get_start_keyboard()
        )