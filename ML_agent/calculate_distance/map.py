
import requests
class SimpleRouteCalculator:
    def __init__(self):
        self.osrm_url = "http://router.project-osrm.org"
        
    def get_route(self, start_coord, end_coord):
        """
        Простая функция для расчета маршрута до рыбацкого места
        """
        try:
            start_str = f"{start_coord[1]},{start_coord[0]}"
            end_str = f"{end_coord[1]},{end_coord[0]}"
            
            url = f"{self.osrm_url}/route/v1/driving/{start_str};{end_str}"
            params = {'overview': 'false'}
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            if data['code'] == 'Ok' and data['routes']:
                route = data['routes'][0]
                return {
                    'success': True,
                    'distance_km': round(route['distance'] / 1000, 2),
                    'duration_minutes': round(route['duration'] / 60, 0),
                    'message': f"Расстояние: {route['distance'] / 1000:.1f} км, время в пути: {route['duration'] / 60:.0f} мин"
                }
        except:
            return {"success": False, "message": "Функция расчета маршрута временно недоступна"}
            

calculator = SimpleRouteCalculator()
route_info = calculator.get_route((59.861234, 30.154855), (60.024322, 31.555976))
print(route_info['message'])