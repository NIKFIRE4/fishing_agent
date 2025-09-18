"""
Клавиатуры для администраторов
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_moderation_keyboard(post_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для модерации постов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{post_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{post_id}")
        ],
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_post_{post_id}"),
            InlineKeyboardButton(text="🔄 Запросить правки", callback_data=f"request_edit_{post_id}")
        ]
    ])
    return keyboard

def get_post_detail_keyboard(post_id: str) -> InlineKeyboardMarkup:
    """Детальная клавиатура для просмотра поста"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{post_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{post_id}")
        ],
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_post_{post_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 К очереди", callback_data="moderation_queue")
        ]
    ])
    return keyboard

def get_queue_navigation_keyboard(posts_data: dict, current_index: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура для навигации по очереди постов"""
    post_ids = list(posts_data.keys())
    
    if not post_ids:
        return get_back_to_admin_keyboard()
    
    keyboard_rows = []
    
    # Кнопки навигации
    nav_row = []
    if current_index > 0:
        prev_id = post_ids[current_index - 1]
        nav_row.append(InlineKeyboardButton(text="⬅️ Пред", callback_data=f"view_post_{prev_id}_{current_index-1}"))
    
    nav_row.append(InlineKeyboardButton(text=f"{current_index + 1}/{len(post_ids)}", callback_data="noop"))
    
    if current_index < len(post_ids) - 1:
        next_id = post_ids[current_index + 1]
        nav_row.append(InlineKeyboardButton(text="След ➡️", callback_data=f"view_post_{next_id}_{current_index+1}"))
    
    if nav_row:
        keyboard_rows.append(nav_row)
    
    # Кнопки действий
    current_post_id = post_ids[current_index]
    keyboard_rows.extend([
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{current_post_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{current_post_id}")
        ],
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_post_{current_post_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад к админ меню", callback_data="back_to_admin")
        ]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Главное меню администратора"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="📋 Очередь модерации", callback_data="moderation_queue")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить меню", callback_data="refresh_admin_menu")
        ],
        [
            InlineKeyboardButton(text="📤 Создать пост", callback_data="create_post"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ])
    return keyboard

def get_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата к админ меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к админ меню", callback_data="back_to_admin")]
    ])
    return keyboard