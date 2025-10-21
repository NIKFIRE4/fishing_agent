from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from endpoints.classes_for_endpoint import ImageRequest, MessageRequest, TelegramSearchRequest, TelegramSearchResponse, BestPlacesRequest, Spot, CompareLocationRequest
from endpoints.endpoints_with_backend import get_all_places_by_type, fetch_best_fishing_places
from model_provider import Model
from relax_analyzer import RelaxAnalyzer, RelaxType
from calculate_distance.encoder import get_similarity, create_semantic_embedding, get_one_name_embedding
from calculate_distance.map import get_route, geocode_name_to_coords
from analyze_and_compare_fish_places import compare_places
import uvicorn
import httpx
from CV_for_person_detect.YOLO_predict import detect_person

app = FastAPI(title="Person Detection API", version="1.0.0")
model = Model() 
analyzer = RelaxAnalyzer(model)
         
@app.get("/")
async def root():
    return {"message": "Person Detection API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "FishAgent ML"}

@app.post("/detect-person")
async def detect_person_endpoint(request: ImageRequest):
    try:
        has_person = detect_person(request.image, conf=0.58)
        
        return JSONResponse(content={
            "person_detected": has_person,
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
    

# @app.get("/places_with_fish")
# async def get_fishing_places():
#     try:
#         data = await get_all_places()
#         return JSONResponse(content=data)
#     except Exception as e:
#         raise HTTPException(status_code=502, detail=f"Error: {e}")
    

@app.post("/get_best_places_with_fish")
async def get_best_fishing_places(request: BestPlacesRequest):
    """
    Принимает JSON с полями target_fish и water_space,
    вызывает fetch_best_fishing_places и возвращает список мест.
    """
    try:
        places = await fetch_best_fishing_places(
            target_fish=request.target_fish,
            water_space=request.water_space
        )
        return JSONResponse(content=places)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка при запросе к API: {exc}"
        )
    

@app.post("/compare_location")
async def compare_location(request: CompareLocationRequest):
    """
    Сравнивает место из сообщения пользователя с существующими местами в базе.
    Поддерживает разные типы отдыха: рыбалка, кемпинг, рыбалка + кемпинг
    Теперь также создает embedding из user_preferences для семантического поиска.
    
    Args:
        request: CompareLocationRequest с полями message и relax_type
        
    Returns:
        JSON с информацией о месте (новое или существующее) + preferences_embedding
    """
    try:
        # Определяем тип отдыха
        relax_type = RelaxType(request.relax_type)
        
        # Анализируем сообщение пользователя
        short_message = analyzer.analyze_existing_place(request.message, relax_type)
        
        target_name = short_message.get("name_location")
        if not target_name:
            raise HTTPException(status_code=400, detail="Не указано название места")
        name_embedding = get_one_name_embedding(target_name)
        target_coords = short_message.get("place_coordinates")
        if not target_coords:
            try:
                target_coords = await geocode_name_to_coords(target_name)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Не удалось определить координаты для места: {target_name}")

        # Получаем все места из базы
        places_by_type = await get_all_places_by_type(relax_type.value)
        
        # Проверяем каждое место
        for place in places_by_type:
            name = place.get("name_place", [None])[0]
            
            # Сначала проверка по названию
            if get_similarity(target_name, name):
                # Если названия совпали, проверяем расстояние
                coords = place.get("coordinates", [])
                if not coords:
                    try:
                        coords = await geocode_name_to_coords(name)
                    except ValueError:
                        continue
                
                route = await get_route(start_coord=coords, end_coord=target_coords)
                distance = route.get('distance_km', float('inf'))
                
                # Если расстояние меньше 2 км, это то же самое место
                if distance < 2:
                    # Обновляем описание существующего места
                    updated_description = place.get("description", "") + " " + request.message
                    updated_short = analyzer.analyze_existing_place(updated_description, relax_type)
                    
                    # Получаем user_preferences (список строк)
                    user_prefs = updated_short.get("user_preferences", [])
                    name_old_embedding = get_one_name_embedding(name)
                    # Создаем embedding из списка строк для семантического поиска
                    preferences_embedding = create_semantic_embedding(user_prefs)
                    
                    # Формируем ответ в зависимости от типа отдыха
                    response_data = {
                        "new_place": False,
                        "name_location": name,
                        "name_embedding": name_old_embedding,
                        "type_of_relax": relax_type.value,
                        "user_preferences": user_prefs,
                        "preferences_embedding": preferences_embedding,
                        "place_coordinates": coords,
                        "description": updated_description
                    }
                    
                    # Добавляем специфичные поля для рыбалки
                    if relax_type in [RelaxType.FISHING, RelaxType.FISHING_AND_CAMPING]:
                        response_data["caught_fishes"] = updated_short.get("caught_fishes", [])
                        response_data["water_space"] = updated_short.get("water_space", [])
                    
                    # Добавляем цену если есть
                    if updated_short.get("wish_price"):
                        response_data["wish_price"] = updated_short.get("wish_price")
                    
                    return JSONResponse(content=response_data)

        # Если ничего не найдено - создаём новое место
        user_prefs = short_message.get("user_preferences", [])
        
        # Создаем embedding из списка строк для семантического поиска
        preferences_embedding = create_semantic_embedding(user_prefs)
        
        response_data = {
            "new_place": True,
            "name_location": target_name,
            "name_embedding": name_embedding,
            "type_of_relax": relax_type.value,
            "user_preferences": user_prefs,
            "preferences_embedding": preferences_embedding,
            "place_coordinates": target_coords,
            "description": request.message
        }
        
        # Добавляем специфичные поля для рыбалки
        if relax_type in [RelaxType.FISHING, RelaxType.FISHING_AND_CAMPING]:
            response_data["caught_fishes"] = short_message.get("caught_fishes", [])
            response_data["water_space"] = short_message.get("water_space", [])
        
        # Добавляем цену если есть
        if short_message.get("wish_price"):
            response_data["wish_price"] = short_message.get("wish_price")
        
        return JSONResponse(content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

    
@app.post("/telegram/search", response_model=TelegramSearchResponse)
async def search_fishing_spots_for_telegram(request: TelegramSearchRequest):
    """
    Основной эндпоинт для поиска мест из Telegram бота.
    
    Новая логика:
    1. Анализирует запрос и извлекает важную информацию
    2. Если указан wish_location - запрашивает места по локации
    3. Если тип "рыбалка" и нет wish_location - запрашивает по рыбе и водоему
    4. Сравнивает векторы user_preferences и формирует топ-10 по семантике
    5. Для топ-10 вычисляет расстояние от пользователя
    6. Формирует финальный рейтинг и возвращает топ-5
    """
    try:
        # Определяем тип отдыха из запроса
        relax_type = RelaxType(request.relax_type) if hasattr(request, 'relax_type') else RelaxType.FISHING
        
        # Используем новую логику сравнения мест
        places_ranked = await compare_places(request.query, relax_type)
        
        # Формируем список результатов
        spots: list[Spot] = []
        for place in places_ranked:
            raw_coords = place.get("coordinates", [])
            raw_user_loc = place.get("location_user", [])
            description_full = place.get("description", "")
            short_desc_obj = place.get("short_description", {})
            
            spot = Spot(
                name=place.get("name_place", [None])[0] or "Неизвестно",
                location_user=raw_user_loc,
                description=description_full,
                short_description=short_desc_obj,
                coordinates=raw_coords,
                distance_km=place.get("distance_km")
            )
            spots.append(spot)
        
        # Оставляем только топ-5 результатов
        spots = spots[:5]
        
        return TelegramSearchResponse(
            success=True,
            spots=spots,
            message=f"Найдено {len(spots)} подходящих мест для отдыха",
        )
        
    except Exception as e:
        print(f"Ошибка при поиске: {e}")
        return TelegramSearchResponse(
            success=False,
            spots=[],
            message=f"Ошибка при поиске: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",  
        port=8001, 
        reload=False
    )
