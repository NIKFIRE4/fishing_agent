"""
FSM состояния для бота
"""
from aiogram.fsm.state import State, StatesGroup

class PostStates(StatesGroup):
    """Состояния FSM для создания поста"""
    waiting_for_date = State()
    waiting_for_photos = State()
    waiting_for_location_name = State()
    waiting_for_location_description = State()
    waiting_for_coordinates = State()

class EditPostStates(StatesGroup):
    """Состояния FSM для редактирования поста администратором"""
    edit_date = State()
    edit_photos = State()
    edit_location_name = State()
    edit_location_description = State()
    edit_coordinates = State()

class ModerationStates(StatesGroup):
    """Состояния для модерации"""
    reviewing_post = State()