import base64
import numpy as np
from PIL import Image
from io import BytesIO
from ultralytics import YOLO
import httpx

async def fetch_fishing_places() -> list[dict]:
    BACKEND_URL = "http://localhost:8002"
    async with httpx.AsyncClient() as client:
        resp = await client.get(BACKEND_URL, timeout=10.0)
        resp.raise_for_status()
        return resp.json()
