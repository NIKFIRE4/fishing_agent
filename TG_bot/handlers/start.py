from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

start_router = Router()

class SearchStates(StatesGroup):
    waiting_for_search_request = State()

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

@start_router.message(SearchStates.waiting_for_search_request)
async def process_search_request(message: Message, state: FSMContext):
    # Здесь будет обработка запроса через ML сервис
    user_request = message.text
    
    # Пока заглушка - в будущем здесь будет вызов ML сервиса
    await message.answer(
        "✅ Ваш запрос принят!\n\n"
        f"Обрабатываем запрос: <i>{user_request}</i>\n\n"
        "🤖 Скоро здесь будет результат от ML сервиса...",
        parse_mode='HTML',
        reply_markup=get_start_keyboard()
    )
    
    # Сбрасываем состояние
    await state.clear()

# Обработчик для возврата в главное меню
@start_router.message(F.text.in_(["🏠 Главное меню", "/menu"]))
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 Главное меню\n\nВыберите одну из опций:",
        reply_markup=get_start_keyboard()
    )