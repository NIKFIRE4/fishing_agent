import httpx
import requests


async def get_route(start_coord: list, end_coord: list) -> dict:
    """
    Асинхронная функция для расчёта маршрута до рыбацкого места через OSRM.
    """
    osrm_url = "http://router.project-osrm.org"
    start_str = f"{start_coord[1]},{start_coord[0]}"
    end_str   = f"{end_coord[1]},{end_coord[0]}"
    url       = f"{osrm_url}/route/v1/driving/{start_str};{end_str}"
    params    = {'overview': 'false'}

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get('code') == 'Ok' and data.get('routes'):
                route = data['routes'][0]
                return {
                    'success': True,
                    'distance_km': round(route['distance'] / 1000, 2),
                    'duration_minutes': round(route['duration'] / 60, 0),
                    'message': (
                        f"Расстояние: {route['distance'] / 1000:.1f} км, "
                        f"время в пути: {route['duration'] / 60:.0f} мин"
                    )
                }
        except httpx.RequestError as e:
            # ошибка сети, таймаут и т.п.
            return {'success': False, 'message': f"Ошибка запроса: {e}"}
        except httpx.HTTPStatusError as e:
            # не-2xx ответ
            return {'success': False, 'message': f"HTTP ошибка: {e.response.status_code}"}
        except Exception:
            return {'success': False, 'message': "Функция расчёта маршрута временно недоступна"}

    
                

async def geocode_name_to_coords(name: str) -> list:
    """
    Функция геокодирования названия места в координаты (широта, долгота)
    Использует Nominatim OpenStreetMap API
    """
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': name,
        'format': 'json',
        'limit': 1,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        results = resp.json()
        if not results:
            raise ValueError(f"Не удалось геокодировать место: {name}")
        lat = float(results[0]['lat'])
        lon = float(results[0]['lon'])
        return [lat, lon]

# async def check_similarity_places_by_coordinates(distance1, distance2):
#     if abs(distance1-distance2) < 10:
#         return True
#     else:
#         return False
    