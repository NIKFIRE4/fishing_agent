
from database.models import async_session, User, SelectedFishingSpot
from sqlalchemy import select, func
from sqlalchemy import Date
from typing import Union, List
from datetime import date
from dotenv import load_dotenv
load_dotenv()
async def get_or_create_user(tg_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Получить или создать пользователя"""
    async with async_session() as session:
        # Ищем существующего пользователя
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Создаем нового пользователя
            user = User(
                tg_id=tg_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        return user

async def save_selected_spot(tg_id: int, spot_data: dict, user_query: str = None, 
                           user_coordinates: list = None, fishing_date: Date = None):
    """Сохранить выбранное место рыбалки"""
    async with async_session() as session:
        # Получаем пользователя
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User with tg_id {tg_id} not found")
        
        # Подготавливаем данные координат
        spot_coords_str = None
        if spot_data.get('coordinates'):
            coords = spot_data['coordinates']
            if isinstance(coords, list) and len(coords) >= 2:
                spot_coords_str = f"{coords[0]},{coords[1]}"
        
        user_coords_str = None
        if user_coordinates and len(user_coordinates) >= 2:
            user_coords_str = f"{user_coordinates[0]},{user_coordinates[1]}"
        
        selected_spot = SelectedFishingSpot(
            user_id=user.id,
            spot_name=spot_data.get('name', 'Неизвестное место'),
            
            spot_coordinates=spot_coords_str,
            user_query=user_query,
            user_coordinates=user_coords_str,
            fishing_date=fishing_date
        )
        
        session.add(selected_spot)
        await session.commit()
        
        return selected_spot

async def get_user_fishing_history(tg_id: int, limit: int = 10):
    """Получить историю выбранных мест пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(SelectedFishingSpot)
            .join(User)
            .where(User.tg_id == tg_id)
            .order_by(SelectedFishingSpot.selected_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
async def count_spot_reservations(
    spot_coordinates: Union[str, List[float]],
    fishing_date: date
) -> int:
    """
    Считает, сколько разных пользователей уже выбирали данную локацию
    spot_coordinates на указанную fishing_date.

    Параметры:
        spot_coordinates: строка "lat,lon" или [lat, lon]
        fishing_date: date — день рыбалки
    Возвращает:
        int — количество уникальных пользователей
    """
    # Приводим координаты к строке, если списком
    if isinstance(spot_coordinates, list):
        spot_coordinates = f"{spot_coordinates[0]},{spot_coordinates[1]}"

    async with async_session() as session:
        # Запрос: считаем уникальных user_id
        stmt = (
            select(func.count(func.distinct(SelectedFishingSpot.user_id)))
            .where(SelectedFishingSpot.spot_coordinates == spot_coordinates)
            .where(SelectedFishingSpot.fishing_date == fishing_date)
        )

        result = await session.execute(stmt)
        count: int = result.scalar_one()  # всегда вернёт число, даже если 0
        return count
