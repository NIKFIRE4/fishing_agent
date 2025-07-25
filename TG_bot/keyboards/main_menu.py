from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_start_keyboard():
    """Создает клавиатуру для стартового меню"""
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