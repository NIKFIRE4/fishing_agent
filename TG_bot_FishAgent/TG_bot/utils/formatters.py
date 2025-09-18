from typing import Dict, List, Optional
from ML_integration import generate_yandex_maps_url
from datetime import date
from database.requests import count_spot_reservations

async def format_spot_description(
    spot: Dict,
    user_coords: Optional[List[float]] = None,
    selected_date: Optional[date] = None
) -> str:
    """Асинхронно форматирует описание места для отображения с улучшенным дизайном."""
    # Заголовок
    text = f"🎣 <b>{spot['name']}</b> 🎣\n"
    text += "────────────────────────────────────\n"

    # Координаты и расстояние
    coords = spot.get('coordinates', [])
    if len(coords) >= 2:
        lat, lon = coords[:2]
        text += f"📍 <b>Координаты:</b> {lat:.6f}, {lon:.6f}\n"
    if spot.get('distance_km') is not None:
        text += f"🚗 <b>Расстояние:</b> {spot['distance_km']:.1f} км\n"

    # Инфо о рыбе и водоеме
    desc = spot.get('short_description', {}) or {}
    fish = desc.get('fish_types')
    if fish:
        text += f"🐟 <b>Рыба:</b> {', '.join(fish)}\n"
    water = desc.get('water_type')
    if water:
        text += f"🌊 <b>Тип водоема:</b> {water}\n"

    text += "\n"

    # Полное описание
    full_desc = spot.get('description', '').strip()
    if full_desc:
        text += f"📝 <b>Описание:</b>\n{full_desc}\n\n"

    # Дополнительная информация: число желающих и статус
    if selected_date and len(coords) >= 2:
        coord_str = f"{coords[0]},{coords[1]}"
        count = await count_spot_reservations(coord_str, selected_date)
        date_str = selected_date.strftime('%d.%m.%Y')
        # Выбираем значок статуса
        if count < 3:
            status_icon = '🟢'
        elif count <= 5:
            status_icon = '🟡'
        else:
            status_icon = '🔴'
        text += (
            f"<b>📊 Доп. инфо на {date_str}:</b> {status_icon} "
            f"На точку хотят выехать {count} человек\n"
        )
        text += "\n"

    # Ссылка на маршрут в Яндекс.Картах
    if user_coords and len(coords) >= 2:
        maps_url = generate_yandex_maps_url(user_coords, coords, spot['name'])
        if maps_url:
            text += f"🗺️ <a href='{maps_url}'>Построить маршрут в Яндекс.Картах</a>\n"

    text += "────────────────────────────────────"
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