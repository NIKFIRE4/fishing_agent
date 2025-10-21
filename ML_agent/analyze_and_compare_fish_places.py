from typing import *
import httpx
from calculate_distance.map import get_route, geocode_name_to_coords
from calculate_distance.encoder import create_semantic_embedding, calculate_semantic_similarity
from endpoints.endpoints_with_backend import get_all_places_by_id, fetch_best_fishing_places, fetch_places_by_location, fetch_all_places_by_type
from model_provider import Model
from calculate_distance.encoder import get_similarity, create_semantic_embedding
from relax_analyzer import RelaxAnalyzer, RelaxType
import random

model = Model()
analyzer = RelaxAnalyzer(model)


async def get_redis_places_embeddings() -> List[Dict]:
    """
    Получает все места с embeddings из Redis.
    Возвращает список вида:
    [
        {
            "id": 1,
            "name_embedding": [...],
            "preferences_embedding": [...],
            "coord_location": [lat, lon]
        },
        ...
    ]
    """
    # TODO: Реализовать получение из Redis
    # Здесь заглушка
    return [
        {
            "id": 1,
            "name_embedding": [0.85, -0.12, 0.44, 0.67],
            "preferences_embedding": [0.82, -0.10, 0.46, 0.65],
            "coord_location": [55.751244, 37.618423]
        },
        {
            "id": 2,
            "name_embedding": [0.33, 0.91, -0.25, 0.18],
            "preferences_embedding": [0.35, 0.89, -0.22, 0.20],
            "coord_location": [59.9311, 30.3609]
        },
        {
            "id": 3,
            "name_embedding": [-0.41, 0.77, 0.59, -0.05],
            "preferences_embedding": [-0.39, 0.75, 0.61, -0.03],
            "coord_location": [60.1699, 24.9384]
        },
        {
            "id": 4,
            "name_embedding": [0.12, -0.66, 0.88, 0.31],
            "preferences_embedding": [0.14, -0.64, 0.90, 0.29],
            "coord_location": [61.5240, 105.3188]
        }
    ]


async def calculate_combined_metric(
    similarity_score: float,
    distance_km: Optional[float],
    similarity_weight: float = 0.6,
    distance_weight: float = 0.4,
    max_distance: float = 100.0
) -> float:
    """
    Вычисляет комбинированную метрику из similarity и distance.
    
    Args:
        similarity_score: Оценка семантического сходства (0-1)
        distance_km: Расстояние в километрах
        similarity_weight: Вес similarity в финальной оценке
        distance_weight: Вес distance в финальной оценке
        max_distance: Максимальное расстояние для нормализации
        
    Returns:
        Комбинированная метрика (0-1)
    """
    # Преобразуем расстояние в оценку (чем ближе, тем лучше)
    if distance_km is not None:
        distance_score = max(0, 1 - (distance_km / max_distance))
    else:
        distance_score = 0.5  # Нейтральная оценка если расстояния нет
    
    # Комбинируем оценки
    combined = (similarity_weight * similarity_score) + (distance_weight * distance_score)
    return combined


async def compare_places(query_user: str, relax_type: RelaxType) -> List[Dict]:
    """
    Логика поиска мест:
    1. Если wish_locations задан:
       - Ищем по векторам названий в Redis
       - Рассчитываем комбинированную метрику (расстояние + preferences)
       - Отправляем топ ID на бэкенд
    2. Если wish_locations не задан и кемпинг:
       - Рассчитываем метрику из Redis (расстояние + preferences)
       - Отправляем топ ID на бэкенд
    3. Если рыбалка без wish_locations:
       - Отправляем caught_fishes и water_space на бэкенд
       - Бэкенд возвращает места с метрикой
    4. Если нет нужных полей:
       - Рандомно берем ID и загружаем из БД
    
    Args:
        query_user: Запрос пользователя
        relax_type: Тип отдыха (рыбалка, кемпинг и т.д.)
        
    Returns:
        Список мест отсортированный по комбинированному рейтингу
    """
    
    # 1. Анализируем запрос пользователя
    short_info = analyzer.analyze_user_query(query_user, relax_type)
    
    wish_locations = short_info.get("wish_location", [])
    caught_fishes = short_info.get("caught_fishes", [])
    water_space = short_info.get("water_space", [])
    user_preferences = short_info.get("user_preferences", [])
    place_name_user = short_info.get("name_place")
    
    # Создаем embedding пользовательских предпочтений один раз
    if user_preferences:
        user_prefs_emb = create_semantic_embedding(user_preferences)
    else:
        user_prefs_emb = create_semantic_embedding(query_user)
    
    # Получаем координаты пользователя (если есть)
    user_coords = None
    if place_name_user:
        try:
            user_coords = await geocode_name_to_coords(place_name_user)
        except Exception as e:
            print(f"Не удалось геокодировать местоположение пользователя: {e}")
    
    # === СЛУЧАЙ 1: wish_locations задан ===
    if wish_locations:
        print("Режим: Поиск по wish_locations")
        
        # Создаем embedding для wish_locations
        wish_locations_emb = create_semantic_embedding(wish_locations)
        
        # Получаем все места из Redis
        all_redis_places = await get_redis_places_embeddings()
        
        # Ищем по векторам названий + рассчитываем комбинированную метрику
        places_with_metrics = []
        
        for place in all_redis_places:
            # Семантическое сходство по названию
            name_similarity = calculate_semantic_similarity(
                place["name_embedding"], 
                wish_locations_emb
            )
            
            # Рассчитываем расстояние
            distance_km = None
            if user_coords and place.get("coord_location"):
                try:
                    route = await get_route(
                        start_coord=user_coords, 
                        end_coord=place["coord_location"]
                    )
                    distance_km = route.get('distance_km')
                except Exception as e:
                    print(f"Ошибка при расчете маршрута: {e}")
            
            # Комбинированная метрика
            combined_metric = await calculate_combined_metric(name_similarity, distance_km)
            
            places_with_metrics.append({
                "id": place["id"],
                "combined_metric": combined_metric,
                "name_similarity": name_similarity,
                "distance_km": distance_km
            })
        
        # Сортируем и берем топ-10
        places_with_metrics.sort(key=lambda x: x["combined_metric"], reverse=True)
        top_places = places_with_metrics[:10]
        
        # Формируем список ID для бэкенда
        places_ids = [place["id"] for place in top_places]
        
        # Получаем полное описание мест с бэкенда
        final_results = await get_all_places_by_id(places_ids)
        
        return final_results
    
    # === СЛУЧАЙ 2: Кемпинг без wish_locations ===
    elif relax_type != RelaxType.FISHING:
        print("Режим: Кемпинг - поиск по preferences из Redis")
        
        # Получаем все места из Redis
        all_redis_places = await get_redis_places_embeddings()
        
        # Рассчитываем комбинированную метрику (preferences + расстояние)
        places_with_metrics = []
        
        for place in all_redis_places:
            # Семантическое сходство по preferences (используем готовый embedding из Redis)
            prefs_similarity = calculate_semantic_similarity(
                place["preferences_embedding"], 
                user_prefs_emb
            )
            
            # Рассчитываем расстояние
            distance_km = None
            if user_coords and place.get("coord_location"):
                try:
                    route = await get_route(
                        start_coord=user_coords, 
                        end_coord=place["coord_location"]
                    )
                    distance_km = route.get('distance_km')
                except Exception as e:
                    print(f"Ошибка при расчете маршрута: {e}")
            
            # Комбинированная метрика
            combined_metric = await calculate_combined_metric(prefs_similarity, distance_km)
            
            places_with_metrics.append({
                "id": place["id"],
                "combined_metric": combined_metric,
                "prefs_similarity": prefs_similarity,
                "distance_km": distance_km
            })
        
        # Сортируем и берем топ-10
        places_with_metrics.sort(key=lambda x: x["combined_metric"], reverse=True)
        top_places = places_with_metrics[:10]
        
        # Формируем список ID для бэкенда
        places_ids = [place["id"] for place in top_places]
        
        # Получаем полное описание мест с бэкенда
        final_results = await get_all_places_by_id(places_ids)
        
        return final_results
    
    # === СЛУЧАЙ 3: Рыбалка с caught_fishes или water_space ===
    elif caught_fishes or water_space:
        print("Режим: Рыбалка - отправляем на бэкенд caught_fishes и water_space")
        
        # Получаем места с бэкенда
        fishing_places = await fetch_best_fishing_places(
            target_fish=caught_fishes,
            water_space=water_space
        )
        
        if not fishing_places:
            return []
        
        # Рассчитываем комбинированную метрику для каждого места
        places_with_metrics = []
        
        for place in fishing_places:
            # Используем готовый preferences_embedding из места (должен быть в Redis/БД)
            place_prefs_emb = place.get("preferences_embedding")
            
            if not place_prefs_emb:
                # Если embedding не сохранен, создаем из user_preferences или description
                place_prefs = place.get("user_preferences", [])
                if place_prefs:
                    place_prefs_emb = create_semantic_embedding(place_prefs)
                else:
                    description = place.get("description", "")
                    if description:
                        place_prefs_emb = create_semantic_embedding(description)
                    else:
                        continue  # Пропускаем место без данных
            
            # Семантическое сходство по preferences
            prefs_similarity = calculate_semantic_similarity(place_prefs_emb, user_prefs_emb)
            
            # Рассчитываем расстояние
            distance_km = None
            place_coords = place.get("coordinates") or place.get("coord_location")
            
            if not place_coords:
                # Пытаемся получить координаты по названию места
                place_name = place.get("name_place", [None])[0] if isinstance(place.get("name_place"), list) else place.get("name_place")
                if place_name:
                    try:
                        place_coords = await geocode_name_to_coords(place_name)
                    except Exception:
                        pass
            
            if user_coords and place_coords:
                try:
                    route = await get_route(
                        start_coord=user_coords,
                        end_coord=place_coords
                    )
                    distance_km = route.get('distance_km')
                except Exception as e:
                    print(f"Ошибка при расчете маршрута: {e}")
            
            # Комбинированная метрика
            combined_metric = await calculate_combined_metric(prefs_similarity, distance_km)
            
            place_with_metric = place.copy()
            place_with_metric["combined_metric"] = combined_metric
            place_with_metric["prefs_similarity"] = prefs_similarity
            place_with_metric["distance_km"] = distance_km
            
            places_with_metrics.append(place_with_metric)
        
        # Сортируем по комбинированной метрике
        places_with_metrics.sort(key=lambda x: x["combined_metric"], reverse=True)
        
        return places_with_metrics
    
    # === СЛУЧАЙ 4: Нет нужных полей - рандомный выбор ===
    else:
        print("Режим: Рандомный выбор мест")
        
        # Получаем все места из Redis
        all_redis_places = await get_redis_places_embeddings()
        
        # Берем рандомные 10 ID
        random_places = random.sample(all_redis_places, min(10, len(all_redis_places)))
        places_ids = [place["id"] for place in random_places]
        
        # Получаем полное описание с бэкенда
        final_results = await get_all_places_by_id(places_ids)
        
        return final_results