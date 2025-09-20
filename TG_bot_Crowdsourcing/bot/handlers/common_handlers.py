"""
Общие обработчики
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from bot.keyboards.user_keyboards import get_main_menu_keyboard
from config import MESSAGES

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    # Сбрасываем состояние при старте
    await state.clear()
    
    await message.answer(
        MESSAGES["welcome"],
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "cancel_post")
async def cancel_post_creation(callback: CallbackQuery, state: FSMContext):
    """Отменяет создание поста"""
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        MESSAGES["cancelled"],
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "info")
async def show_info(callback: CallbackQuery):
    """Показывает информацию о боте"""
    await callback.answer()
    
    info_text = (
        "ℹ️ ИНФОРМАЦИЯ О БОТЕ\n\n"
        "🏕️ Этот бот предназначен для публикации постов о походах в канале Camp Place\n\n"
        "КАК ЭТО РАБОТАЕТ:\n"
        "1. Вы создаёте пост с информацией о походе\n"
        "2. Пост отправляется на модерацию\n"
        "3. Администратор проверяет и публикует пост в канале\n"
        "4. Вы получаете уведомление о результате\n\n"
        "ЧТО НУЖНО ДЛЯ ПОСТА:\n"
        "• Дата похода\n"
        "• Название места\n"
        "• Фотографии (1-10 штук)\n"
        "• Описание локации\n"
        "• Координаты места\n\n"
        "На любом этапе можно нажать \"❌ Отменить\" для начала заново"
    )
    
    # Обрабатываем исключение если сообщение уже содержит такой же текст
    try:
        await callback.message.edit_text(
            info_text,
            reply_markup=get_main_menu_keyboard()
        )
    except Exception:
        # Если не удалось отредактировать (например, контент уже такой же),
        # просто игнорируем ошибку - пользователь уже видит нужную информацию
        pass