from typing import Dict, List
from ML_integration import generate_yandex_maps_url

def format_spot_description(spot: Dict, user_coords: List[float] = None) -> str:
    """Форматирует описание места для отображения"""
    text = f"🎣 <b>{spot['name']}</b>\n\n"
    
    # Координаты
    coordinates = spot.get('coordinates', [])
    if coordinates and len(coordinates) >= 2:
        lat, lon = coordinates[0], coordinates[1]
        text += f"📍 <b>Координаты:</b> {lat:.6f}, {lon:.6f}\n"
    
    # Расстояние
    if spot.get('distance_km') is not None:
        text += f"🚗 <b>Расстояние:</b> {spot['distance_km']:.1f} км\n"
    
    # Информация о рыбе и водоеме
    short_desc = spot.get('short_description', {})
    if isinstance(short_desc, dict):
        if short_desc.get('fish_types'):
            fish_list = ', '.join(short_desc['fish_types'])
            text += f"🐟 <b>Рыба:</b> {fish_list}\n"
        if short_desc.get('water_type'):
            text += f"🌊 <b>Тип водоема:</b> {short_desc['water_type']}\n"
    
    text += "\n"
    
    # Описание места
    description = spot.get('description', '')
    if description:
        text += f"📝 <b>Описание:</b>\n{description}\n\n"
    
    # Ссылка на маршрут
    if user_coords and coordinates:
        maps_url = generate_yandex_maps_url(user_coords, coordinates, spot['name'])
        if maps_url:
            text += f"🗺️ <a href='{maps_url}'>Построить маршрут в Яндекс.Картах</a>\n"
    
    return text

def format_history_text(history, limit=5):
    """Форматирует историю поездок"""
    if not history:
        return (
            "📚 <b>История ваших поездок</b>\n\n"
            "У вас пока нет сохраненных мест для рыбалки.\n"
            "Начните поиск, чтобы выбрать первое место!"
        )
    
    history_text = "📚 <b>Последние поездки</b>\n\n"
    
    for i, spot in enumerate(history[:limit], 1):
        date_str = spot.selected_at.strftime("%d.%m")
        history_text += f"<b>{i}. {spot.spot_name}</b>\n"
        
        if spot.fishing_date:
            fishing_date_str = spot.fishing_date.strftime("%d.%m.%Y")
            history_text += f"🎣 {fishing_date_str}\n"
        else:
            history_text += f"📅 {date_str}\n"
        
        history_text += "\n"
    
    if len(history) > limit:
        history_text += f"И еще {len(history) - limit} поездок...\n\n"
    
    return history_text