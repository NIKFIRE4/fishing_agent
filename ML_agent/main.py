from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from endpoints.classes_for_endpoint import ImageRequest, MessageRequest, TelegramSearchRequest, TelegramSearchResponse, BestPlacesRequest, FishingSpot
from endpoints.endpoints_with_backend import fetch_fishing_places, fetch_best_fishing_places
from my_openrouter_chat import FishingAnalyzer, Model
from calculate_distance.encoder import get_similarity
from calculate_distance.map import get_route, geocode_name_to_coords
from analyze_and_compare_fish_places import compare_fish_places
import uvicorn
import httpx
from CV_for_person_detect.YOLO_predict import detect_person

app = FastAPI(title="Person Detection API", version="1.0.0")
model = Model() 
analyzer = FishingAnalyzer(model)
         
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
    

@app.get("/places_with_fish")
async def get_fishing_places():
    try:
        data = await fetch_fishing_places()
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error: {e}")
    

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
        # httpx.RequestError и httpx.HTTPStatusError оба наследуются от HTTPError
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка при запросе к API: {exc}"
        )
    
@app.post("/get_short_description_for_existing_location")
async def get_short_description_for_existing_location(request: MessageRequest):
    try:
        short_message = analyzer.analyze_existing_places(request.message)
        
        return JSONResponse(content={
            "short_message": short_message,
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"get short description failed: {str(e)}")

@app.post("/compare_fishing_places")
async def compare_fishing_places(request: MessageRequest):
    try:
        short_message = analyzer.analyze_existing_places(request.message)
        target_names = short_message.get("name_place", [])
        if not target_names:
            raise HTTPException(status_code=400, detail="Не указано ни одного места для сравнения")
        target_name = target_names[0] 

        target_coords = short_message.get("coordinates")
        if not target_coords:
            target_coords = await geocode_name_to_coords(target_name)

        fishing_places = await fetch_fishing_places()
                  
        for place in fishing_places:
            name = place.get("name_place", [None])[0]
            coords = place.get("coordinates", [])

            if not coords:
                try:
                    coords = await geocode_name_to_coords(name)
                except ValueError:
                    continue

            if get_similarity(target_name, name):
                short_description = analyzer.analyze_existing_places(place.get("description", "None") + request.message)
                return JSONResponse(content={
                    "new_place": False,
                    "name_place": place.get("name_place"),
                    "coordinates": coords,
                    "short_description": short_description,
                    "description": place.get("description", "None") + request.message,
                })

            route = await get_route(start_coord=coords, end_coord=target_coords)
            if route.get('distance_km') < 2:
                short_description = analyzer.analyze_existing_places(place.get("description", "None") + request.message)
                return JSONResponse(content={
                    "new_place": False,
                    "name_place": place.get("name_place"),
                    "coordinates": coords,
                    "short_description": short_description,
                    "description": place.get("description", "None") + request.message,
                })

        # Создание нового места только если ничего не найдено после всех итераций
        short_description = analyzer.analyze_existing_places(request.message)
        return JSONResponse(content={
            "new_place": True,
            "name_place": target_name,
            "coordinates": target_coords,
            "short_description": short_description,
            "description": request.message,
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
    
@app.post("/telegram/search", response_model=TelegramSearchResponse)
async def search_fishing_spots_for_telegram(request: TelegramSearchRequest):
    """
    Основной эндпоинт для поиска мест рыбалки из Telegram бота.
    Теперь использует compare_fish_places для расчёта и сортировки по distance_km.
    """
    try:
        short_info = analyzer.analyze_query_users(request.query)

        fishing_places = await fetch_best_fishing_places(
            short_info.get("caught_fishes", []),
            short_info.get("water_space", [])
        )

        places_with_distance: list[dict] = await compare_fish_places(request.query, fishing_places)

        spots: list[FishingSpot] = []
        for place in places_with_distance:

            raw_coords = place.get("coordinates", [])         # [lat, lon]
            raw_user_loc = place.get("location_user", [])     # [lat, lon]
            description_full = place.get("description", "")
            short_desc_obj = place.get("short_description", {})
            
            spot = FishingSpot(
                name=place.get("name_place", [None])[0] or "Неизвестно",
                # Если в short_description лежит dict с ключом "short_description"
                location_user = raw_user_loc,
                description=description_full,
                short_description = short_desc_obj,
                coordinates=raw_coords,
                distance_km= place.get("distance_km")  # уже рассчитано
            )
            spots.append(spot)
            
        # 5. Дополнительно сортируем по релевантности
        #    Сортировка по distance уже сделана, но мы здесь можем учитывать ещё текстовый запрос
        #spots = sort_spots_by_relevance(spots, short_info, user_coords=None)
        # 6. Оставляем только топ-5 результатов
        spots = spots[:5]

        return TelegramSearchResponse(
            success=True,
            spots=spots,
            message=f"Найдено {len(spots)} подходящих мест для рыбалки",
        )

    except Exception as e:
        # В случае ошибки возвращаем пустой список с описанием
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