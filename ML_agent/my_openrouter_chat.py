from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import List, Optional
import os

class FishingRequest(BaseModel):
    wish_fishes: Optional[List[str]] = None
    fishing_place: Optional[str] = None
    location_user: Optional[str] = None
    wish_radius_km: Optional[int] = None

llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model="deepseek/deepseek-r1-0528:free",
    temperature=0.7,
)

structured_llm = llm.with_structured_output(FishingRequest)

messages = [
    SystemMessage(content="Извлеки информацию о рыбалке из сообщения пользователя"),
    HumanMessage(content="Я хочу порыбачить в 20 км от станции метро Автово в Санкт-Петербурге, желательно поймать щуку или окуня, предпочтительно на речке,где это можно сделать?"),
]

result = structured_llm.invoke(messages)

print(f"Желаемая рыба: {result.wish_fishes}")
print(f"Место рыбалки: {result.fishing_place}")
print(f"Местоположение: {result.location_user}")
print(f"Радиус: {result.wish_radius_km} км")