from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from endpoints.classes_for_endpoint import ImageRequest
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
    BACKEND_URL = "http://192.168.0.103:8002"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(BACKEND_URL, timeout=10.0)
            response.raise_for_status()  # если статус >=400 — бросит exception
            data = response.json()
            print(data)
            return JSONResponse(content=data)
    
    except (httpx.HTTPError, ValueError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка при получении рыбацких мест: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",  
        port=8001, 
        reload=False
    )