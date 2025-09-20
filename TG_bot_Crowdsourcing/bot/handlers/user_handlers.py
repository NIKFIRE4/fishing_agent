"""
Обработчики для пользователей
"""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import asyncio
import time
from bot.states.states import PostStates
from bot.keyboards.user_keyboards import (
    get_cancel_keyboard, get_photos_keyboard, 
    get_confirm_keyboard, get_main_menu_keyboard
)
from config import ADMIN_ID
from bot.services.post_service import PostService
from bot.services.moderation_service import ModerationService
from bot.utils.helpers import validate_date
from config import MAX_PHOTOS, MIN_DESCRIPTION_LENGTH, MAX_DESCRIPTION_LENGTH, MESSAGES
from ..database.user_service import UserService
from bot.utils import admin
router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in admin.ADMIN_IDS
@router.callback_query(F.data == "create_post")
async def start_post_creation(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс создания поста"""
    await callback.answer()
    
    await callback.message.edit_text(
        "📅 Давайте создадим пост о вашем походе!\n\n"
        "Для начала укажите **дату похода** в формате **ДД.ММ.ГГГГ**\n"
        "Например: `15.09.2025`",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(PostStates.waiting_for_date)

@router.message(PostStates.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    """Обрабатывает дату похода"""
    print(f"DEBUG: Получено сообщение в состоянии waiting_for_date: '{message.text}'")
    
    date_obj = validate_date(message.text)
    
    if not date_obj:
        await message.answer(
            "❌ Неверный формат даты!\n"
            "Пожалуйста, используйте формат **ДД.ММ.ГГГГ**\n"
            "Например: `15.09.2025`",
            reply_markup=get_cancel_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    print(f"DEBUG: Дата валидна: {date_obj}")
    
    # Сохраняем дату
    await state.update_data(date=message.text)
    
    await message.answer(
        "📸 Отлично! Теперь отправьте **фотографии** с похода.\n\n"
        f"Вы можете отправить от 1 до {MAX_PHOTOS} фотографий.\n"
        "Отправляйте фото по одному, затем нажмите **\"✅ Закончить загрузку\"**",
        reply_markup=get_photos_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(PostStates.waiting_for_photos)
    await state.update_data(photos=[])

@router.message(PostStates.waiting_for_photos, F.photo)
async def process_photos(message: Message, state: FSMContext):
    """Обрабатывает фотографии.
    Поддержка медиагрупп: клавиатура показывается только один раз —
    после получения последнего фото альбома (debounce по media_group_id).
    """
    data = await state.get_data()
    photos = data.get('photos', [])

    if len(photos) >= MAX_PHOTOS:
        await message.answer(
            f"❌ Максимум {MAX_PHOTOS} фотографий!",
            reply_markup=get_photos_keyboard()
        )
        return

    # file_id самого большого размера фото
    photo_file_id = message.photo[-1].file_id
    photos.append(photo_file_id)
    await state.update_data(photos=photos)

    media_group_id = getattr(message, "media_group_id", None)

    # Если фото часть медиагруппы (альбома) — не отвечаем сразу,
    # а делаем "дебаунс": ждём короткую паузу и проверяем, не пришло ли ещё фото с тем же album id.
    if media_group_id:
        ts = time.time()
        # сохраняем идентификатор альбома и метку времени обновления
        await state.update_data(last_media_group_id=media_group_id, album_update_time=ts)

        # короткая пауза — даём время прийти остальным сообщениям альбома
        await asyncio.sleep(0.6)  # можно тонко подбирать (0.4..1.0) в зависимости от задержек

        # заново получаем состояние — проверяем, не обновилась ли метка времени
        sdata = await state.get_data()
        if sdata.get("album_update_time") == ts:
            # Метка не изменилась — это последний вызов для данного альбома.
            total = len(sdata.get("photos", []))
            await message.answer(
                f"✅ Фото добавлено! Всего загружено: **{total}/{MAX_PHOTOS}**\n"
                f"Отправьте ещё фото или нажмите **\"✅ Закончить загрузку\"**",
                reply_markup=get_photos_keyboard(),
                parse_mode="Markdown"
            )
        else:
            # Пришли новые элементы альбома — другой обработчик их обработает/отправит итог.
            return

    else:
        # Обычное одиночное фото — отвечаем сразу
        await message.answer(
            f"✅ Фото добавлено! Всего загружено: **{len(photos)}/{MAX_PHOTOS}**\n"
            f"Отправьте ещё фото или нажмите **\"✅ Закончить загрузку\"**",
            reply_markup=get_photos_keyboard(),
            parse_mode="Markdown"
        )

@router.callback_query(F.data == "finish_photos")
async def finish_photos(callback: CallbackQuery, state: FSMContext):
    """Завершает загрузку фотографий"""
    await callback.answer()
    
    data = await state.get_data()
    photos = data.get('photos', [])
    
    if not photos:
        await callback.message.edit_text(
            "❌ Загрузите хотя бы одно фото!",
            reply_markup=get_photos_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "📍 Теперь укажите **название места** похода.\n\n"
        "Например: 'Финский залив, Канонерский остров', 'Ладожское озеро, Назия', 'Лемболово'",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(PostStates.waiting_for_location_name)

@router.message(PostStates.waiting_for_location_name)
async def process_location_name(message: Message, state: FSMContext):
    """Обрабатывает название места"""
    location_name = message.text.strip()
    
    if len(location_name) < 2:
        await message.answer(
            "❌ Название места слишком короткое! Минимум 2 символа.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    if len(location_name) > 100:
        await message.answer(
            "❌ Название места слишком длинное! Максимум 100 символов.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(location_name=location_name)
    
    await message.answer(
        "📝 Отлично! Теперь **опишите локацию** подробнее.\n\n"
        "Укажите особенности маршрута, что интересного можно увидеть, "
        "сложность похода и другие полезные детали.\n\n"
        f"Минимум {MIN_DESCRIPTION_LENGTH} символов, максимум {MAX_DESCRIPTION_LENGTH}",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(PostStates.waiting_for_location_description)

@router.message(PostStates.waiting_for_location_description)
async def process_location_description(message: Message, state: FSMContext):
    """Обрабатывает описание локации"""
    description = message.text.strip()
    
    if len(description) < MIN_DESCRIPTION_LENGTH:
        await message.answer(
            f"❌ Описание слишком короткое! Минимум {MIN_DESCRIPTION_LENGTH} символов.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    if len(description) > MAX_DESCRIPTION_LENGTH:
        await message.answer(
            f"❌ Описание слишком длинное! Максимум {MAX_DESCRIPTION_LENGTH} символов.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(location_description=description)
    
    await message.answer(
        "🗺️ Отлично! Теперь укажите **координаты локации**.\n\n"
        "Можете отправить их в любом формате:\n"
        "• Десятичные градусы: `55.7558, 37.6173`\n"
        "• Градусы/минуты: `55°45'21\"N 37°37'02\"E`\n"
        "• Ссылку на карты\n"
        "• Или просто отправьте геолокацию 📍",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(PostStates.waiting_for_coordinates)

@router.message(PostStates.waiting_for_coordinates, F.location)
async def process_location_coordinates(message: Message, state: FSMContext, bot: Bot):
    """Обрабатывает координаты из геолокации"""
    coordinates = f"{message.location.latitude}, {message.location.longitude}"
    await finish_post_creation(message, state, coordinates, bot)

@router.message(PostStates.waiting_for_coordinates)
async def process_text_coordinates(message: Message, state: FSMContext, bot: Bot):
    """Обрабатывает координаты из текста"""
    coordinates = message.text.strip()
    
    if len(coordinates) < 3:
        await message.answer(
            "❌ Координаты слишком короткие! Укажите корректные координаты.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await finish_post_creation(message, state, coordinates, bot)

async def finish_post_creation(message: Message, state: FSMContext, coordinates: str, bot: Bot):
    """Завершает создание поста и показывает предварительный просмотр"""
    data = await state.get_data()
    
    # Сохраняем координаты
    await state.update_data(coordinates=coordinates)
    
    # Показываем предварительный просмотр
    preview_text = (
        "📋 **ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР ПОСТА**\n\n"
        f"📅 **Дата похода:** {data['date']}\n"
        f"📸 **Количество фото:** {len(data['photos'])}\n"
        f"📍 **Название места:** {data['location_name']}\n"
        f"📝 **Описание:**\n{data['location_description']}\n"
        f"🗺️ **Координаты:** {coordinates}\n\n"
        "Всё верно? Можете отправить пост на модерацию или отредактировать."
    )
    
    await message.answer(
        preview_text,
        reply_markup=get_confirm_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "confirm_post")
async def confirm_post(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Подтверждает и отправляет пост на модерацию"""
    await callback.answer()
    
    await UserService.get_or_create_user(callback.from_user)
    data = await state.get_data()
    
    # Создаем пост
    post_id, post_data = PostService.create_post(
        user=callback.from_user,
        date=data['date'],
        photos=data['photos'],
        location_name=data['location_name'],
        location_description=data['location_description'],
        coordinates=data['coordinates']
    )
    
    # Отправляем на модерацию
    moderation_service = ModerationService(bot)
    await moderation_service.send_to_moderation(post_id, post_data)
    
    # Уведомляем пользователя
    await callback.message.edit_text(
        MESSAGES["post_created"],
        reply_markup=get_main_menu_keyboard()
    )
    
    await state.clear()

@router.callback_query(F.data == "edit_post")
async def edit_post(callback: CallbackQuery, state: FSMContext):
    """Позволяет отредактировать пост (начать заново)"""
    await callback.answer()
    
    await callback.message.edit_text(
        "✏️ Хорошо, давайте создадим пост заново!\n\n"
        "Укажите **дату похода** в формате **ДД.ММ.ГГГГ**\n"
        "Например: `15.09.2025`",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(PostStates.waiting_for_date)

# Обработчики для состояния ожидания фото, если пришло не фото
@router.message(PostStates.waiting_for_photos)
async def handle_non_photo_in_photos_state(message: Message, state: FSMContext):
    """Обрабатывает не-фото в состоянии ожидания фото"""
    await message.answer(
        "📸 Пожалуйста, отправьте фотографию или нажмите **\"✅ Закончить загрузку\"**",
        reply_markup=get_photos_keyboard(),
        parse_mode="Markdown"
    )

# ОБЩИЙ ОБРАБОТЧИК - ДОЛЖЕН БЫТЬ В САМОМ КОНЦЕ!
@router.message()
async def handle_unknown_messages(message: Message, state: FSMContext):
    """Обрабатывает неизвестные сообщения (fallback)"""
    current_state = await state.get_state()
    
    # Если это админ в админском состоянии - не обрабатываем здесь
    if is_admin(message.from_user.id) and current_state and str(current_state).startswith('EditPostStates'):
        return
    
    if current_state is None:
        await message.answer(
            "Используйте кнопки меню для навигации:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # Если пользователь в пользовательском состоянии, но прислал не то сообщение
        if str(current_state).startswith('PostStates'):
            await message.answer(
                "❓ Не понял ваше сообщение. Используйте кнопки или следуйте инструкциям.",
                reply_markup=get_cancel_keyboard()
            )
        else:
            # Для всех остальных состояний
            await message.answer(
                "❓ Не понял ваше сообщение. Используйте кнопки меню:",
                reply_markup=get_main_menu_keyboard()
            )