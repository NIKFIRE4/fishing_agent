from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from endpoints.classes_for_endpoint import ImageRequest, MessageRequest
from endpoints.endpoints_with_backend import fetch_fishing_places
from my_openrouter_chat import get_important_information
from calculate_distance.encoder import get_similarity
from calculate_distance.map import SimpleRouteCalculator
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
        short_message = get_important_information(request.message)
        places = await fetch_fishing_places()
        for place in places:
            target_locs = short_message.get("name_place", [])
            locs = place.get("name_place", [])
            bool_predict_encoder = get_similarity(target_locs[0], locs[0])
            if bool_predict_encoder:
                return JSONResponse(content={
                        "new_place": False,
                        "name_place": place.get("name_place", []),
                        "coordinates": place.get("coordinates", []),
                        "description": place.get("description", []) + request.message
                    })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",  
        port=8001, 
        reload=False
    )