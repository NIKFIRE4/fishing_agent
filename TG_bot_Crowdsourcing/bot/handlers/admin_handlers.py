"""
Обработчики для администраторов
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import os
from bot.services.post_service import PostService
from bot.services.moderation_service import ModerationService
from bot.keyboards.admin_keyboards import (
    get_admin_main_menu, get_back_to_admin_keyboard, 
    get_queue_navigation_keyboard
)
from bot.keyboards.user_keyboards import get_main_menu_keyboard
from bot.states.states import EditPostStates
from bot.utils.helpers import validate_date
from config import MIN_DESCRIPTION_LENGTH, MAX_DESCRIPTION_LENGTH
from config import ADMIN_ID
from bot.utils import admin
logger = logging.getLogger(__name__)
router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in admin.ADMIN_IDS

@router.message(Command("admin"))
async def admin_command(message: Message):
    """Команда /admin - открывает админ панель"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора")
        return
    
    username = message.from_user.username or message.from_user.first_name
    
    await message.answer(
        f"ПАНЕЛЬ АДМИНИСТРАТОРА\n\n"
        f"Добро пожаловать, @{username}!\n"
        "Выберите действие:",
        reply_markup=get_admin_main_menu()
    )

@router.callback_query(F.data == "back_to_admin")
async def back_to_admin_menu(callback: CallbackQuery):
    """Возврат к админ меню"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    await callback.answer()
    
    username = callback.from_user.username or callback.from_user.first_name
    
    await callback.message.edit_text(
        f"ПАНЕЛЬ АДМИНИСТРАТОРА\n\n"
        f"Добро пожаловать, @{username}!\n"
        "Выберите действие:",
        reply_markup=get_admin_main_menu()
    )

@router.callback_query(F.data == "refresh_admin_menu")
async def refresh_admin_menu(callback: CallbackQuery):
    """Обновление админ меню"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    await callback.answer("Меню обновлено")
    
    username = callback.from_user.username or callback.from_user.first_name
    
    await callback.message.edit_text(
        f"ПАНЕЛЬ АДМИНИСТРАТОРА\n\n"
        f"Добро пожаловать, @{username}!\n"
        "Выберите действие:",
        reply_markup=get_admin_main_menu()
    )

@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery):
    """Переход в главное меню"""
    await callback.answer()
    
    await callback.message.edit_text(
        "ГЛАВНОЕ МЕНЮ\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery):
    """Показывает статистику для администратора"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    await callback.answer()
    
    memory_stats = PostService.get_statistics()
    
    # Получаем статистику пользователей из БД
    from ..database.user_service import UserService
    db_stats = await UserService.get_all_users_stats()
    
    stats_text = (
        f"СТАТИСТИКА БОТА\n\n"
        f"ПОСТЫ:\n"
        f"• На модерации: {memory_stats['total_posts']}\n"
        f"• Всего опубликовано: {db_stats['total_posts']}\n"
        f"• Всего отправлено: {db_stats['total_submitted']}\n"
        f"• Процент одобрения: {db_stats['approval_rate']}%\n\n"
        f"ПОЛЬЗОВАТЕЛИ:\n"
        f"• Всего зарегистрировано: {db_stats['total_users']}\n"
        f"• Новых за месяц: {db_stats['recent_users']}\n"
    )
    
    if db_stats['top_users']:
        stats_text += "\nТОП АВТОРЫ:\n"
        for user in db_stats['top_users'][:5]:
            stats_text += f"• {user['username']}: {user['posts_count']} постов\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Недавние пользователи", callback_data="recent_users")],
        [InlineKeyboardButton(text="🔙 Назад к админ меню", callback_data="back_to_admin")]
    ])
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_back_to_admin_keyboard()
    )

@router.callback_query(F.data == "moderation_queue")
async def show_moderation_queue(callback: CallbackQuery):
    """Показывает очередь модерации с навигацией"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    await callback.answer()
    
    stats = PostService.get_statistics()
    
    if stats['total_posts'] == 0:
        await callback.message.edit_text(
            "ОЧЕРЕДЬ МОДЕРАЦИИ ПУСТА\n\n"
            "Нет постов, ожидающих модерации.",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    
    # Показываем первый пост в очереди
    post_ids = list(stats['all_posts'].keys())
    first_post_id = post_ids[0]
    await show_post_details(callback, first_post_id, 0)

async def show_post_details(callback_or_message, post_id: str, index: int):
    """Показывает детали поста для модерации"""
    post_data = PostService.get_post(post_id)
    if not post_data:
        if hasattr(callback_or_message, 'message'):
            await callback_or_message.message.edit_text(
                "Пост не найден",
                reply_markup=get_back_to_admin_keyboard()
            )
        else:
            await callback_or_message.edit_text(
                "Пост не найден", 
                reply_markup=get_back_to_admin_keyboard()
            )
        return
    
    stats = PostService.get_statistics()
    
    post_text = (
        f"ПОСТ НА МОДЕРАЦИИ ({index + 1}/{stats['total_posts']})\n\n"
        f"Автор: @{post_data.username}\n"
        f"Дата похода: {post_data.date}\n"
        f"Место: {post_data.location_name}\n"
        f"Описание: {post_data.location_description[:200]}{'...' if len(post_data.location_description) > 200 else ''}\n"
        f"Координаты: {post_data.coordinates}\n"
        f"Фото: {len(post_data.photos)} шт.\n"
        f"Создан: {post_data.timestamp.strftime('%d.%m.%Y %H:%M')}"
    )
    
    # Отправляем/редактируем текст с клавиатурой
    if hasattr(callback_or_message, 'message'):
        await callback_or_message.message.edit_text(
            post_text,
            reply_markup=get_queue_navigation_keyboard(stats['all_posts'], index)
        )
    else:
        await callback_or_message.edit_text(
            post_text,
            reply_markup=get_queue_navigation_keyboard(stats['all_posts'], index)
        )
    
    # Отправляем фото отдельно
    if post_data.photos:
        bot = callback_or_message.bot if hasattr(callback_or_message, 'bot') else callback_or_message.message.bot
        chat_id = callback_or_message.from_user.id if hasattr(callback_or_message, 'from_user') else callback_or_message.message.chat.id
        
        try:
            if len(post_data.photos) == 1:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=post_data.photos[0]
                )
            else:
                media = [InputMediaPhoto(media=photo_id) for photo_id in post_data.photos]
                await bot.send_media_group(
                    chat_id=chat_id,
                    media=media
                )
        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")

@router.callback_query(F.data.startswith("view_post_"))
async def view_specific_post(callback: CallbackQuery):
    """Просмотр конкретного поста по индексу"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    await callback.answer()
    
    try:
        # Парсим данные: view_post_{post_id}_{index}
        parts = callback.data.split("_")
        post_id = "_".join(parts[2:-1])  # ID может содержать подчеркивания
        index = int(parts[-1])
        
        await show_post_details(callback, post_id, index)
    except Exception as e:
        logger.error(f"Ошибка просмотра поста: {e}")
        await callback.message.edit_text(
            "Ошибка загрузки поста",
            reply_markup=get_back_to_admin_keyboard()
        )

@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """Обработчик для кнопок-заглушек"""
    await callback.answer()

@router.callback_query(F.data.startswith("edit_post_"))
async def start_edit_post(callback: CallbackQuery, state: FSMContext):
    """Начинает редактирование поста"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    post_id = callback.data.replace("edit_post_", "")
    post_data = PostService.get_post(post_id)
    
    if not post_data:
        await callback.answer("Пост не найден", show_alert=True)
        return
    
    await callback.answer()
    
    # Сохраняем ID редактируемого поста
    await state.update_data(editing_post_id=post_id)
    
    edit_menu = (
        f"РЕДАКТИРОВАНИЕ ПОСТА\n\n"
        f"Автор: @{post_data.username}\n"
        f"Текущая дата: {post_data.date}\n"
        f"Текущее место: {post_data.location_name}\n"
        f"Текущее описание: {post_data.location_description[:100]}{'...' if len(post_data.location_description) > 100 else ''}\n"
        f"Текущие координаты: {post_data.coordinates}\n"
        f"Фотографий: {len(post_data.photos)}\n\n"
        f"Что хотите изменить?"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Дату", callback_data=f"edit_date_{post_id}"),
            InlineKeyboardButton(text="📍 Место", callback_data=f"edit_name_{post_id}")
        ],
        [
            InlineKeyboardButton(text="📝 Описание", callback_data=f"edit_location_{post_id}"),
            InlineKeyboardButton(text="🗺️ Координаты", callback_data=f"edit_coords_{post_id}")
        ],
        [
            InlineKeyboardButton(text="✅ Сохранить и одобрить", callback_data=f"approve_{post_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="moderation_queue")
        ]
    ])
    
    await callback.message.edit_text(edit_menu, reply_markup=keyboard)

@router.callback_query(F.data.startswith("edit_date_"))
async def edit_post_date(callback: CallbackQuery, state: FSMContext):
    """Редактирование даты поста"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    post_id = callback.data.replace("edit_date_", "")
    await callback.answer()
    
    await state.update_data(editing_post_id=post_id)
    await state.set_state(EditPostStates.edit_date)
    
    await callback.message.edit_text(
        "Введите новую дату в формате ДД.ММ.ГГГГ:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"edit_post_{post_id}")]
        ])
    )

@router.callback_query(F.data.startswith("edit_name_"))
async def edit_post_name(callback: CallbackQuery, state: FSMContext):
    """Редактирование названия места"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    post_id = callback.data.replace("edit_name_", "")
    await callback.answer()
    
    await state.update_data(editing_post_id=post_id)
    await state.set_state(EditPostStates.edit_location_name)
    
    await callback.message.edit_text(
        "Введите новое название места:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"edit_post_{post_id}")]
        ])
    )

@router.callback_query(F.data.startswith("edit_location_"))
async def edit_post_location(callback: CallbackQuery, state: FSMContext):
    """Редактирование описания поста"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    post_id = callback.data.replace("edit_location_", "")
    await callback.answer()
    
    await state.update_data(editing_post_id=post_id)
    await state.set_state(EditPostStates.edit_location_description)
    
    await callback.message.edit_text(
        "Введите новое описание локации:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"edit_post_{post_id}")]
        ])
    )

@router.callback_query(F.data.startswith("edit_coords_"))
async def edit_post_coordinates(callback: CallbackQuery, state: FSMContext):
    """Редактирование координат поста"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    post_id = callback.data.replace("edit_coords_", "")
    await callback.answer()
    
    await state.update_data(editing_post_id=post_id)
    await state.set_state(EditPostStates.edit_coordinates)
    
    await callback.message.edit_text(
        "Введите новые координаты:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"edit_post_{post_id}")]
        ])
    )

# Обработчики для состояний редактирования
@router.message(EditPostStates.edit_date)
async def process_edit_date(message: Message, state: FSMContext, bot: Bot):
    """Обработка новой даты"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора")
        await state.clear()
        return
    
    # Проверяем, что мы действительно в состоянии редактирования
    current_state = await state.get_state()
    if current_state != EditPostStates.edit_date:
        await message.answer("Ошибка состояния. Попробуйте начать редактирование заново.")
        await state.clear()
        return
    
    date_obj = validate_date(message.text)
    if not date_obj:
        await message.answer(
            "❌ Неверный формат даты! Используйте формат ДД.ММ.ГГГГ\n"
            "Например: 15.09.2025"
        )
        return
    
    data = await state.get_data()
    post_id = data.get('editing_post_id')
    
    if not post_id:
        await message.answer("Ошибка: ID поста не найден")
        await state.clear()
        return
    
    # Обновляем пост
    post_data = PostService.get_post(post_id)
    if not post_data:
        await message.answer("Ошибка: пост не найден")
        await state.clear()
        return
    
    post_data.date = message.text
    await message.answer(f"✅ Дата обновлена на: {message.text}")
    await state.clear()
    
    # Возвращаемся к меню редактирования
    await return_to_edit_menu(message, post_id, bot)

@router.message(EditPostStates.edit_location_name)
async def process_edit_location_name(message: Message, state: FSMContext, bot: Bot):
    """Обработка нового названия места"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора")
        await state.clear()
        return
    
    current_state = await state.get_state()
    if current_state != EditPostStates.edit_location_name:
        await message.answer("Ошибка состояния. Попробуйте начать редактирование заново.")
        await state.clear()
        return
    
    location_name = message.text.strip()
    
    if len(location_name) < 2:
        await message.answer("❌ Название места слишком короткое! Минимум 2 символа.")
        return
    
    if len(location_name) > 100:
        await message.answer("❌ Название места слишком длинное! Максимум 100 символов.")
        return
    
    data = await state.get_data()
    post_id = data.get('editing_post_id')
    
    if not post_id:
        await message.answer("Ошибка: ID поста не найден")
        await state.clear()
        return
    
    post_data = PostService.get_post(post_id)
    if not post_data:
        await message.answer("Ошибка: пост не найден")
        await state.clear()
        return
    
    post_data.location_name = location_name
    await message.answer("✅ Название места обновлено!")
    await state.clear()
    
    await return_to_edit_menu(message, post_id, bot)

@router.message(EditPostStates.edit_location_description)
async def process_edit_location_description(message: Message, state: FSMContext, bot: Bot):
    """Обработка нового описания"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора")
        await state.clear()
        return
    
    current_state = await state.get_state()
    if current_state != EditPostStates.edit_location_description:
        await message.answer("Ошибка состояния. Попробуйте начать редактирование заново.")
        await state.clear()
        return
    
    description = message.text.strip()
    
    if len(description) < MIN_DESCRIPTION_LENGTH:
        await message.answer(f"❌ Описание слишком короткое! Минимум {MIN_DESCRIPTION_LENGTH} символов.")
        return
    
    if len(description) > MAX_DESCRIPTION_LENGTH:
        await message.answer(f"❌ Описание слишком длинное! Максимум {MAX_DESCRIPTION_LENGTH} символов.")
        return
    
    data = await state.get_data()
    post_id = data.get('editing_post_id')
    
    if not post_id:
        await message.answer("Ошибка: ID поста не найден")
        await state.clear()
        return
    
    post_data = PostService.get_post(post_id)
    if not post_data:
        await message.answer("Ошибка: пост не найден")
        await state.clear()
        return
    
    post_data.location_description = description
    await message.answer("✅ Описание обновлено!")
    await state.clear()
    
    await return_to_edit_menu(message, post_id, bot)

@router.message(EditPostStates.edit_coordinates)
async def process_edit_coordinates(message: Message, state: FSMContext, bot: Bot):
    """Обработка новых координат"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора")
        await state.clear()
        return
    
    current_state = await state.get_state()
    if current_state != EditPostStates.edit_coordinates:
        await message.answer("Ошибка состояния. Попробуйте начать редактирование заново.")
        await state.clear()
        return
    
    coordinates = message.text.strip()
    
    if len(coordinates) < 3:
        await message.answer("❌ Координаты слишком короткие! Укажите корректные координаты.")
        return
    
    data = await state.get_data()
    post_id = data.get('editing_post_id')
    
    if not post_id:
        await message.answer("Ошибка: ID поста не найден")
        await state.clear()
        return
    
    post_data = PostService.get_post(post_id)
    if not post_data:
        await message.answer("Ошибка: пост не найден")
        await state.clear()
        return
    
    post_data.coordinates = coordinates
    await message.answer("✅ Координаты обновлены!")
    await state.clear()
    
    await return_to_edit_menu(message, post_id, bot)

async def return_to_edit_menu(message: Message, post_id: str, bot: Bot):
    """Возвращает к меню редактирования поста"""
    post_data = PostService.get_post(post_id)
    if not post_data:
        await message.answer("Ошибка: пост не найден")
        return
    
    edit_menu = (
        f"РЕДАКТИРОВАНИЕ ПОСТА\n\n"
        f"Автор: @{post_data.username}\n"
        f"Текущая дата: {post_data.date}\n"
        f"Текущее место: {post_data.location_name}\n"
        f"Текущее описание: {post_data.location_description[:100]}{'...' if len(post_data.location_description) > 100 else ''}\n"
        f"Текущие координаты: {post_data.coordinates}\n"
        f"Фотографий: {len(post_data.photos)}\n\n"
        f"Что хотите изменить?"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Дату", callback_data=f"edit_date_{post_id}"),
            InlineKeyboardButton(text="📍 Место", callback_data=f"edit_name_{post_id}")
        ],
        [
            InlineKeyboardButton(text="📝 Описание", callback_data=f"edit_location_{post_id}"),
            InlineKeyboardButton(text="🗺️ Координаты", callback_data=f"edit_coords_{post_id}")
        ],
        [
            InlineKeyboardButton(text="✅ Сохранить и одобрить", callback_data=f"approve_{post_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="moderation_queue")
        ]
    ])
    
    await message.answer(edit_menu, reply_markup=keyboard)

@router.callback_query(F.data.startswith("request_edit_"))
async def request_edit(callback: CallbackQuery, bot: Bot):
    """Запрашивает правки от автора (старое поведение)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    post_id = callback.data.replace("request_edit_", "")
    
    moderation_service = ModerationService(bot)
    success = await moderation_service.request_edit(post_id)
    
    if success:
        await callback.answer("Автор уведомлен о необходимости правок")
        # Возвращаемся к очереди модерации
        await show_moderation_queue(callback)
    else:
        await callback.answer("Ошибка при запросе правок", show_alert=True)

@router.callback_query(F.data.startswith("approve_"))
async def approve_post(callback: CallbackQuery, bot: Bot):
    """Одобряет пост и публикует в канале"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав для модерации", show_alert=True)
        return
    
    post_id = callback.data.replace("approve_", "")
    
    moderation_service = ModerationService(bot)
    success = await moderation_service.approve_post(post_id)
    
    if success:
        await callback.answer("Пост опубликован!")
        # Возвращаемся к очереди модерации
        await show_moderation_queue(callback)
    else:
        await callback.answer("Ошибка при публикации", show_alert=True)

@router.callback_query(F.data.startswith("reject_"))
async def reject_post(callback: CallbackQuery, bot: Bot):
    """Отклоняет пост"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав для модерации", show_alert=True)
        return
    
    post_id = callback.data.replace("reject_", "")
    
    moderation_service = ModerationService(bot)
    success = await moderation_service.reject_post(post_id)
    
    if success:
        await callback.answer("Пост отклонен")
        # Возвращаемся к очереди модерации
        await show_moderation_queue(callback)
    else:
        await callback.answer("Ошибка при отклонении", show_alert=True)

# УДАЛЯЕМ СТАРЫЙ ОБРАБОТЧИК - он больше не нужен
# Все кнопки уже используют правильный формат edit_post_, request_edit_ и т.д.
# 
# @router.callback_query(F.data.startswith("edit_") & ~F.data.startswith("edit_post_") & ~F.data.startswith("edit_date_") & ~F.data.startswith("edit_name_") & ~F.data.startswith("edit_location_") & ~F.data.startswith("edit_coords_"))
# async def old_edit_handler(callback: CallbackQuery, bot: Bot):
#     """УДАЛЕН - больше не нужен"""
#     pass

# Дополнительные команды (скрытые для быстрого доступа)
@router.message(Command("stats"))
async def show_stats_command(message: Message):
    """Быстрая команда статистики"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для просмотра статистики")
        return
    
    stats = PostService.get_statistics()
    
    stats_text = (
        f"СТАТИСТИКА БОТА\n\n"
        f"Постов на модерации: {stats['total_posts']}\n"
        f"Уникальных пользователей: {stats['unique_users']}"
    )
    
    await message.answer(stats_text)

@router.message(Command("myid"))
async def get_my_id_command(message: Message):
    """Быстрая команда для получения ID"""
    user_info = (
        f"Ваша информация:\n\n"
        f"Telegram ID: {message.from_user.id}\n"
        f"Username: @{message.from_user.username or 'не указан'}\n"
        f"Имя: {message.from_user.first_name or 'не указано'}\n"
        f"Статус: {'Администратор' if is_admin(message.from_user.id) else 'Пользователь'}"
    )
    
    await message.answer(user_info)

# Обработчик только для админских состояний - НЕ общий обработчик!
@router.message(EditPostStates.edit_date)
@router.message(EditPostStates.edit_location_name)  
@router.message(EditPostStates.edit_location_description)
@router.message(EditPostStates.edit_coordinates)
async def handle_admin_non_text_in_edit_states(message: Message, state: FSMContext):
    """Обработчик НЕ-текстовых сообщений в админских состояниях редактирования"""
    if not is_admin(message.from_user.id):
        return
    
    current_state = await state.get_state()
    
    # Если администратор в состоянии редактирования, но прислал не текст
    if current_state and str(current_state).startswith('EditPostStates') and message.content_type != 'text':
        await message.answer(
            "❌ В режиме редактирования можно отправлять только текстовые сообщения.\n"
            "Отправьте текст или используйте кнопку 'Отменить'."
        )
        return