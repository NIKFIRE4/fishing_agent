"""
Клавиатуры для пользователей
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню пользователя"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создать пост", callback_data="create_post")],
        [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info")]
    ])
    return keyboard

def get_persistent_keyboard() -> ReplyKeyboardMarkup:
    """Постоянная клавиатура внизу экрана (всегда видна)"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Создать пост")],
            [KeyboardButton(text="ℹ️ Информация")]
        ],
        resize_keyboard=True,  # Автоматически подстраивает размер кнопок
        persistent=True  # Клавиатура остаётся видимой всегда
    )
    return keyboard

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_post")]
    ])
    return keyboard

def get_photos_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для управления фотографиями"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Закончить загрузку", callback_data="finish_photos")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_post")]
    ])
    return keyboard

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_post"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_post")
        ],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_post")]
    ])
    return keyboard