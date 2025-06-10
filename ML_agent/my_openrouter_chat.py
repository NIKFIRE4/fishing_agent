
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
import json
from langchain.prompts import ChatPromptTemplate
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model="deepseek/deepseek-r1-0528:free",
    temperature=0.7,
)

# response = llm.invoke([HumanMessage(content="как дела?")])
# print(response.content)

messages = [
    SystemMessage(content="""На основе пользовательского сообщения «{question}» верни строго валидный JSON, где:\n"
    "- wish_fishes: массив строк (породы рыб), которые хочет поймать пользователь, или null,\n"
    "- fishing_place: строка с названием места (озеро, река, море и т. д.), или null,\n"
    "- location_user: строка с местом где рыбак живет и откуда ему хочется порыбачить, или null,\n"
    "- wish_radius_km: число (максимальное расстояние в километрах, на которое пользователь готов поехать), или null.\n"
    "Если какая-то из этих деталей отсутствует в вопросе, используй null.\n"
    "Пример формата ответа:\n"
    {"wish_fishes": ["щука", "окунь"], "fishing_place": "озеро Малое Светлое", "location_user": "Санкт-Петербург", "wish_radius_km": 50}
    Верни ТОЛЬКО JSON (без лишних пояснений)."""
    
),
    HumanMessage(content="Я хочу порыбачить в 20 км от станции метро Автово в Санкт-Петербурге, желательно поймать щуку или окуня, предпочтительно на речке,где это можно сделать?"),
]
response = llm.invoke(messages)
print(response.content)