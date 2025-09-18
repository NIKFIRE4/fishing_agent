from typing import *
import httpx
from calculate_distance.map import get_route, geocode_name_to_coords
from endpoints.endpoints_with_backend import fetch_fishing_places, fetch_best_fishing_places
from my_openrouter_chat import FishingAnalyzer, Model

model = Model()
analyzer = FishingAnalyzer(model)

async def compare_fish_places(query_user: str, fishing_places: List[Dict]) -> List[Dict]:
    """
    Для каждого места из fishing_places пытаемся определить расстояние от пользователя
    и возвращаем список мест, отсортированный по distance_km (от самых близких к самым далеким).
    """
    intresting_spots: List[Dict] = []
    
    # 1. Анализ запроса пользователя (например, наименование отправной точки)
    short_info = analyzer.analyze_query_users(query_user)
    
    # 2. Получаем координаты пользователя (если они есть в анализе)
    user_coords = None
    place_name_user = short_info.get("name_place", [None])[0]
    if place_name_user:
        try:
            user_coords = await geocode_name_to_coords(place_name_user)
        except Exception as e:
            # Если геокодинг не удался — оставляем user_coords = None
            # Можно сюда добавить логирование ошибки e, если нужно
            pass
    
    # 3. Проходим по каждому месту из списка
    for place in fishing_places:
        distance_km = None
        
        # 3.1. Получаем или вычисляем координаты места
        place_coords = place.get("coordinates", [])
        if not place_coords:
            # Если координат нет, пробуем геокодировать по имени
            place_name = place.get("name_place", [None])[0]
            if place_name:
                try:
                    place_coords = await geocode_name_to_coords(place_name)
                except Exception:
                    # Если и это не удалось — пропускаем место
                    continue
        
        # 3.2. Если есть и координаты пользователя, и координаты места, пробуем маршрут
        if user_coords and place_coords:
            try:
                route = await get_route(start_coord=user_coords, end_coord=place_coords)
                distance_km = route.get('distance_km')
            except Exception:
                # Если не удалось получить маршрут — оставляем distance_km = None
                pass
        
        # 3.3. Добавляем в результирующий список, сохраняя все поля места,
        #      и добавляя ключ 'distance_km'
        spot_with_distance = place.copy()
        spot_with_distance['distance_km'] = distance_km
        spot_with_distance["location_user"] = user_coords
        intresting_spots.append(spot_with_distance)
    
    # 4. Сортируем по distance_km:
    #    - места с известным числовым distance_km — по возрастанию;
    #    - места с distance_km=None считаются самыми «дальними» (будут в конце).
    sorted_spots = sorted(
        intresting_spots,
        key=lambda x: x['distance_km'] if x['distance_km'] is not None else float('inf')
    )
    
    return sorted_spots
