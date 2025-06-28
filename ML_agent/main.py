from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from endpoints.classes_for_endpoint import ImageRequest, MessageRequest
from endpoints.endpoints_with_backend import fetch_fishing_places
from my_openrouter_chat import get_important_information
from calculate_distance.encoder import get_similarity
from calculate_distance.map import get_route, geocode_name_to_coords
import uvicorn
import httpx
from CV_for_person_detect.YOLO_predict import detect_person

app = FastAPI(title="Person Detection API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Person Detection API is running"}

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
    

@app.post("/get_short_description")
async def get_short_description(request: MessageRequest):
    try:
        short_message = get_important_information(request.message)
        
        return JSONResponse(content={
            "short_message": short_message,
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"get short description failed: {str(e)}")

@app.post("/compare_fishing_places")
async def compare_fishing_places(request: MessageRequest):
    try:
        # получаем краткую инфу и список имен мест из сообщения
        short_message = get_important_information(request.message)
        target_names = short_message.get("name_place", [])
        if not target_names:
            raise HTTPException(status_code=400, detail="Не указано ни одного места для сравнения")
        target_name = target_names[0]

        # геокодим новое место, если нет координат в сообщении
        target_coords = short_message.get("coordinates")
        if not target_coords:
            target_coords = await geocode_name_to_coords(target_name)

        fishing_places = await fetch_fishing_places()

        
        for place in fishing_places:
            name = place.get("name_place", [None])[0]
            coords = place.get("coordinates", [])

            # если у существующего места нет координат, геокодируем его
            if not coords:
                try:
                    coords = await geocode_name_to_coords(name)
                except ValueError:
                    # пропускаем, если не можем геокодировать
                    continue

            # проверка на схожесть по энкодеру
            if get_similarity(target_name, name):
                short_description = get_important_information(place.get("description", []) + request.message)
                return JSONResponse(content={
                    "new_place": False,
                    "name_place": place.get("name_place"),
                    "coordinates": coords,
                    "short_description": short_description,
                    "description": place.get("description", []) + request.message,
                })

            # если не совпало, считаем маршрут от существующего до нового места
            route = await get_route(start_coord=coords, end_coord=target_coords)
            if route.get('distance_km') < 2:
                short_description = get_important_information(place.get("description", []) + request.message)
                return JSONResponse(content={"new_place": False,
                                             "name_place": place.get("name_place"),
                                             "coordinates": coords,
                                             "short_description": short_description,
                                             "description": place.get("description", []) + request.message,
                                             })
            else:
                short_description = get_important_information(request.message)
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

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",  
        port=8001, 
        reload=False
    )