from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import List, Optional, Any
import os

class FishingRequest(BaseModel):
    fishing_location: Optional[List[str]] = []
    caught_fishes: Optional[List[str]] = []
    coordinates: Optional[List[float]] = []
    water_space: Optional[List[str]] = []

llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model="deepseek/deepseek-r1-0528:free",
    temperature=0.7,
)

def get_important_information(message: str):
    structured_llm = llm.with_structured_output(FishingRequest)
    messages = [
    SystemMessage(content="Извлеки информацию о рыбалке из сообщения пользователя, в переменную fishing_location нужно записать место где человек рыбачил, например ['Река Вуокса Выборгский район'], в переменную caught_fishes ты должен записать рыб, которых пользователь поймал на этой локации, например ['щука', 'окунь'], в переменную coordinates нужно записать координаты точки где рыбак ловил рыбу, обычно это выглядит как-то так: [59.861234, 30.154855] В переменную water_space нужно записать вид водоема в котором человек рыбачил, например ['озеро'] или ['река']."),
    HumanMessage(content=message)]
    result = structured_llm.invoke(messages)
    return {
        "fishing_location": result.fishing_location,
        "coordinates": result.coordinates,
        "caught_fishes": result.caught_fishes,
        "water_space": result.water_space,
    }

