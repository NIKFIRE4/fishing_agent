from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

def get_main_menu_inline_keyboard():
    """Inline клавиатура главного меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎣 Начать поиск мест", callback_data="start_search")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about_us")]
    ])

def get_history_keyboard():
    """Клавиатура для истории"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎣 Новый поиск", callback_data="start_search")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])