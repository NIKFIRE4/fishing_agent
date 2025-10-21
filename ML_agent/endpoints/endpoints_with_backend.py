import httpx

# BACKEND_URL = "http://parsing_service:8002/api/Places"
BACKEND_URL = "http://localhost:8002"


# async def fetch_all_places_by_type() -> list[dict]:
#     """
#     Получает все места из базы данных.
    
#     Returns:
#         Список всех мест
#     """
#     async with httpx.AsyncClient() as client:
#         resp = await client.get(BACKEND_URL, timeout=10.0)
#         resp.raise_for_status()
#         return resp.json()

async def get_all_places_by_type(
    type_relax: str
) -> list[dict]:
    
    payload = {
        "type_relax": type_relax
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(BACKEND_URL, json=payload)
        resp.raise_for_status()
        return resp.json()
    
async def get_all_places_by_id(
    places_ids: list[int]
) -> list[dict]:
    payload = {
        "place_ids": places_ids
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{BACKEND_URL}/places_by_ids", json=payload)
        resp.raise_for_status()
        return resp.json()

async def fetch_best_fishing_places(
    target_fish: list[str],
    water_space: list[str]
) -> list[dict]:
    """
    Получает места для рыбалки, отфильтрованные по видам рыбы и типу водоема.
    
    Args:
        target_fish: Список видов рыбы
        water_space: Список типов водоемов
        
    Returns:
        Список подходящих мест для рыбалки
    """
    payload = {
        "target_fish": target_fish,
        "water_space": water_space,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(BACKEND_URL, json=payload)
        resp.raise_for_status()
        return resp.json()


async def fetch_places_by_location(locations: list[str]) -> list[dict]:
    """
    Получает места по конкретным названиям локаций.
    
    Args:
        locations: Список названий локаций (например, ["Ладожское озеро", "Финский залив"])
        
    Returns:
        Список мест в указанных локациях
    """
    payload = {
        "locations": locations
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{BACKEND_URL}/by_location", json=payload)
        resp.raise_for_status()
        return resp.json()