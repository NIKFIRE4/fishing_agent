import os
import time
import logging
import requests
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv

# --------------------- 📌 Модели ---------------------
class LocationIntent(BaseModel):
    intent_type: str
    activity: Optional[str]
    place_type: Optional[List[str]]
    reference_location: Optional[str]
    specific_preferences: Optional[List[str]]
    cuisine_type: Optional[List[str]]
    budget_level: Optional[str]
    time_preference: Optional[str]

class YandexPlace(BaseModel):  # теперь GeoapifyPlace
    name: str
    address: str
    coordinates: List[float]
    categories: List[str]
    distance: Optional[float] = None

class PlaceRecommendation(BaseModel):
    place: YandexPlace
    match_score: float
    recommendation_reason: str
    route_url: Optional[str] = None

# --------------------- 🔮 AI-провайдер ---------------------
class ModelProvider:
    def __init__(self, name: str, llm, priority: int = 0):
        self.name = name
        self.llm = llm
        self.priority = priority
        self.is_available = True
        self.failure_count = 0
        self.max_failures = 1

    def test_connection(self) -> bool:
        try:
            msgs = [SystemMessage(content="Test"), HumanMessage(content="Hi")]
            self.llm.invoke(msgs)
            self.failure_count = 0
            self.is_available = True
            return True
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.max_failures:
                self.is_available = False
            return False

# -------------------- 🌐 Geoapify сервис --------------------
class GeoapifyService:
    BASE_URL = "https://api.geoapify.com/v2/places"
    def __init__(self, api_key: str, pause: float = 0.3):
        self.api_key = api_key
        self.pause = pause

    def search_places(self, lat: float, lon: float, radius: int = 2000,
                      categories: Optional[str] = None, limit: int = 20) -> List[Dict]:
        params = {
            "apiKey": self.api_key,
            "filter": f"circle:{lon},{lat},{radius}",
            "limit": limit,
            "lang": "ru"
        }
        if categories:
            params["categories"] = categories
        resp = requests.get(self.BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        time.sleep(self.pause)
        places = []
        for feat in data.get("features", []):
            prop = feat.get("properties", {})
            places.append({
                "name": prop.get("name", ""),
                "address": prop.get("formatted", ""),
                "coordinates": [feat["geometry"]["coordinates"][1],
                                feat["geometry"]["coordinates"][0]],
                "categories": prop.get("categories", []),
                "distance": prop.get("distance")
            })
        return places

# -------------------- 🔍 Intent анализ --------------------
class IntentAnalyzer:
    def __init__(self, providers: List[ModelProvider]):
        self.providers = providers

    def analyze(self, text: str) -> LocationIntent:
        prompt = "Проанализируй запрос пользователя и верни LocationIntent"
        for prov in sorted(self.providers, key=lambda p: p.priority):
            if prov.is_available and prov.test_connection():
                llm = prov.llm.with_structured_output(LocationIntent)
                try:
                    return llm.invoke([SystemMessage(content=prompt),
                                       HumanMessage(content=text)])
                except Exception:
                    continue
        return LocationIntent(intent_type="find_nearby",
                              activity=None,
                              place_type=None,
                              reference_location=text,
                              specific_preferences=None,
                              cuisine_type=None,
                              budget_level=None,
                              time_preference=None)

# -------------------- ⭐ Рекомендатель --------------------
class PlaceRecommendationEngine:
    def __init__(self, geo_service: GeoapifyService, analyzer: IntentAnalyzer):
        self.geo = geo_service
        self.analyzer = analyzer

    def _score(self, place: Dict, intent: LocationIntent) -> float:
        score = 0.3
        if intent.activity:
            if any(intent.activity in c for c in place["categories"]):
                score += 0.3
        if place.get("distance") is not None:
            score += max(0, 0.2 - place["distance"]/10000)
        return min(score, 1.0)

    def _reason(self, place: Dict, intent: LocationIntent, score: float) -> str:
        parts = [f"Совпадение {int(score*100)}%"]
        if place.get("distance") is not None:
            parts.append(f"примерно {int(place['distance'])} м отсюда")
        return ", ".join(parts)

    def get_recommendations(self, intent: LocationIntent, center: Tuple[float,float],
                            limit: int = 5) -> List[PlaceRecommendation]:
        places = self.geo.search_places(center[0], center[1],
                                        categories="catering.restaurant,catering.cafe", limit=limit*2)
        recs = []
        for p in places:
            score = self._score(p, intent)
            recs.append(PlaceRecommendation(
                place=YandexPlace(**p),
                match_score=score,
                recommendation_reason=self._reason(p, intent, score),
                route_url=f"https://www.openstreetmap.org/directions?engine=osrm_car&route={center[0]},{center[1]};{p['coordinates'][0]},{p['coordinates'][1]}"
            ))
        recs.sort(key=lambda x: x.match_score, reverse=True)
        return recs[:limit]

# -------------------- 🚀 Сервис --------------------
class Service:
    def __init__(self):
        load_dotenv()
        logging.basicConfig(level=logging.INFO)
        self.providers = []
        if os.getenv("CAILA_API_KEY"):
            caila = ChatOpenAI(
                openai_api_key=os.getenv("CAILA_API_KEY"),
                openai_api_base="https://caila.io/api/adapters/openai",
                model="just-ai/openai-proxy/gpt-4o-mini",
                temperature=0.7,
            )
            self.providers.append(ModelProvider("caila", caila, priority=1))
        if not self.providers:
            raise RuntimeError("нужен CAILA_API_KEY")
        self.analyzer = IntentAnalyzer(self.providers)
        geo_key = os.getenv("GEOAPIFY_API_KEY")
        if not geo_key:
            raise RuntimeError("Добавьте GEOAPIFY_API_KEY в .env")
        self.geo = GeoapifyService(geo_key)
        self.engine = PlaceRecommendationEngine(self.geo, self.analyzer)

    def run(self):
        print("🔍 Введите запрос и координаты центра (lat, lon):")
        text = input("Запрос: ").strip()
        lat = float(input("Latitude: "))
        lon = float(input("Longitude: "))
        intent = self.analyzer.analyze(text)
        recs = self.engine.get_recommendations(intent, (lat, lon), limit=5)
        if not recs:
            print("Ничего не найдено")
        for i, r in enumerate(recs, 1):
            p = r.place
            print(f"{i}. {p.name} — {p.address} (категории: {','.join(p.categories)})\n   {r.recommendation_reason}\n   Карта: {r.route_url}\n")

if __name__ == "__main__":
    Service().run()
