from typing import *
import httpx
from calculate_distance.map import get_route, geocode_name_to_coords
from calculate_distance.encoder import create_semantic_embedding, calculate_semantic_similarity
from endpoints.endpoints_with_backend import get_all_places_by_id, fetch_best_fishing_places, fetch_places_by_location, get_all_places_by_type
from model_provider import Model
from calculate_distance.encoder import get_similarity, create_semantic_embedding
from relax_analyzer import RelaxAnalyzer, RelaxType
from redis_bd import RedisManager
import random
from dotenv import load_dotenv

load_dotenv()
model = Model()
analyzer = RelaxAnalyzer(model)
redis_manager = RedisManager()

async def get_redis_places_embeddings(type_of_relax: str) -> List[Dict]:
    """
    Получает все места с embeddings из Redis.
    """
    try:
        places = redis_manager.get_all_places(type_of_relax)
        return places if places else []
    except Exception as e:
        print(f"Ошибка при получении данных из Redis: {e}")
        return []


async def calculate_combined_metric(
    similarity_score: float,
    distance_km: Optional[float],
    similarity_weight: float = 0.5,
    distance_weight: float = 0.5,
    max_distance: float = 100.0
) -> float:
    """
    Вычисляет комбинированную метрику из similarity и distance.
    """
    if distance_km is not None:
        distance_score = max(0, 1 - (distance_km / max_distance))
    else:
        distance_score = 0.5
    
    combined = (similarity_weight * similarity_score) + (distance_weight * distance_score)
    return combined


async def compare_places(query_user: str) -> List[Dict]:
    """
    Логика поиска мест с возвратом location_user и distance_km для телеграм-бота.
    """
    relax_type = analyzer.determine_relax_type(query_user)
    short_info = analyzer.analyze_user_query(query_user, relax_type)
    
    location_user = short_info.get("location_user")
    type_of_relax = short_info.get("type_of_relax")
    wish_locations = short_info.get("wish_location", [])
    caught_fishes = short_info.get("caught_fishes", [])
    water_space = short_info.get("water_space", [])
    user_preferences = short_info.get("user_preferences", [])
   
    
    # Создаем embedding пользовательских предпочтений
    if user_preferences:
        user_prefs_emb = create_semantic_embedding(user_preferences)
    else:
        user_prefs_emb = create_semantic_embedding(query_user)
    
    # Получаем координаты пользователя
    user_coords = None
    if location_user:
        try:
            user_coords = await geocode_name_to_coords(location_user)
        except Exception as e:
            print(f"Не удалось геокодировать местоположение пользователя: {e}")
    elif location_user:
        try:
            user_coords = await geocode_name_to_coords(location_user)
        except Exception as e:
            print(f"Не удалось геокодировать местоположение пользователя: {e}")
    
    # === СЛУЧАЙ 1: wish_locations задан ===
    if wish_locations:
        print("Режим: Поиск по wish_locations")
        
        wish_locations_emb = create_semantic_embedding(wish_locations)
        all_redis_places = await get_redis_places_embeddings(type_of_relax)
        
        places_with_metrics = []
        
        for place in all_redis_places:
            name_similarity = calculate_semantic_similarity(
                place["name_embedding"], 
                wish_locations_emb
            )
            
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
            
            combined_metric = await calculate_combined_metric(name_similarity, distance_km)
            
            places_with_metrics.append({
                "id": place["location_id"],
                "combined_metric": combined_metric,
                "name_similarity": name_similarity,
                "distance_km": distance_km
            })
        
        places_with_metrics.sort(key=lambda x: x["combined_metric"], reverse=True)
        top_places = places_with_metrics[:10]
        places_ids = [place["id"] for place in top_places]
        
        # Получаем полное описание мест с бэкенда
        full_places = await get_all_places_by_id(places_ids)
        
        # Обогащаем данные метриками
        metrics_dict = {item["id"]: item for item in top_places}
        for place in full_places:
            place_id = place.get("id") or place.get("place_id")
            metrics = metrics_dict.get(place_id, {})
            place["location_user"] = user_coords  # Передаем координаты, а не название
            place["distance_km"] = metrics.get("distance_km")
        
        return full_places
    
    # === СЛУЧАЙ 2: Кемпинг без wish_locations ===
    elif type_of_relax == RelaxType.CAMPING:
        print("Режим: Кемпинг - поиск по preferences из Redis")
        
        all_redis_places = await get_redis_places_embeddings(type_of_relax)
        places_with_metrics = []
        
        for place in all_redis_places:
            prefs_similarity = calculate_semantic_similarity(
                place["preferences_embedding"], 
                user_prefs_emb
            )
            
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
            
            combined_metric = await calculate_combined_metric(prefs_similarity, distance_km)
            
            places_with_metrics.append({
                "id": place["location_id"],
                "combined_metric": combined_metric,
                "prefs_similarity": prefs_similarity,
                "distance_km": distance_km
            })
        
        places_with_metrics.sort(key=lambda x: x["combined_metric"], reverse=True)
        top_places = places_with_metrics[:10]
        places_ids = [place["id"] for place in top_places]
        
        # Получаем полное описание мест с бэкенда
        full_places = await get_all_places_by_id(places_ids)
        
        # Обогащаем данные метриками
        metrics_dict = {item["id"]: item for item in top_places}
        for place in full_places:
            place_id = place.get("id")
            metrics = metrics_dict.get(place_id, {})
            place["location_user"] = user_coords
            place["distance_km"] = metrics.get("distance_km")
        
        return full_places
    
    # === СЛУЧАЙ 3: Рыбалка с caught_fishes или water_space ===
    elif caught_fishes or water_space:
        print("Режим: Рыбалка - отправляем на бэкенд caught_fishes и water_space")
        
        fishing_places = await fetch_best_fishing_places(
            target_fish=caught_fishes,
            water_space=water_space
        )
        
        if not fishing_places:
            return []
        
        places_with_metrics = []
        
        for place in fishing_places:
            place_prefs_emb = place.get("preferences_embedding")
            
            if not place_prefs_emb:
                place_prefs = place.get("user_preferences", [])
                if place_prefs:
                    place_prefs_emb = create_semantic_embedding(place_prefs)
                else:
                    description = place.get("description", "")
                    if description:
                        place_prefs_emb = create_semantic_embedding(description)
                    else:
                        continue
            
            prefs_similarity = calculate_semantic_similarity(place_prefs_emb, user_prefs_emb)
            
            distance_km = None
            place_coords = place.get("coordinates") or place.get("coord_location")
            
            if not place_coords:
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
            
            combined_metric = await calculate_combined_metric(prefs_similarity, distance_km)
            
            # Добавляем вычисленные поля
            place["location_user"] = user_coords  # Передаем координаты, а не название
            place["distance_km"] = distance_km
            place["combined_metric"] = combined_metric
            
            places_with_metrics.append(place)
        
        places_with_metrics.sort(key=lambda x: x["combined_metric"], reverse=True)
        
        return places_with_metrics
    
    # === СЛУЧАЙ 4: Нет нужных полей - рандомный выбор ===
    else:
        print("Режим: Рандомный выбор мест")
        
        all_redis_places = await get_redis_places_embeddings(type_of_relax)
        random_places = random.sample(all_redis_places, min(10, len(all_redis_places)))
        places_ids = [place["location_id"] for place in random_places]
        
        # Получаем полное описание с бэкенда
        full_places = await get_all_places_by_id(places_ids)
        
        # Добавляем location_user и distance_km
        for place in full_places:
            place["location_user"] = user_coords  # Передаем координаты, а не название
            place_coords = place.get("coordinates") or place.get("coord_location")
            
            distance_km = None
            if user_coords and place_coords:
                try:
                    route = await get_route(
                        start_coord=user_coords,
                        end_coord=place_coords
                    )
                    distance_km = route.get('distance_km')
                except Exception:
                    pass
            
            place["distance_km"] = distance_km
        
        return full_places