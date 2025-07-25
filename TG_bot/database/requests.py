
from database.models import async_session, User, SelectedFishingSpot
from sqlalchemy import select
from sqlalchemy import Date
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
