import base64
import numpy as np
from PIL import Image
from io import BytesIO
from ultralytics import YOLO
import httpx
BACKEND_URL = "http://localhost:8002"
async def fetch_fishing_places() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(BACKEND_URL, timeout=10.0)
        resp.raise_for_status()
        return resp.json()

async def fetch_best_fishing_places(
    target_fish: list[str],
    water_space: list[str]
) -> list[dict]:
    payload = {
        "target_fish": target_fish,
        "water_space": water_space,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(BACKEND_URL, json=payload)
        resp.raise_for_status()
        return resp.json()