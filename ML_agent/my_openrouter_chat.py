from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import os
import logging
from dotenv import load_dotenv

class FishingRequest(BaseModel):
    name_place: Optional[List[str]] = []
    caught_fishes: Optional[List[str]] = []
    coordinates: Optional[List[float]] = []
    water_space: Optional[List[str]] = []

load_dotenv()

class ModelProvider:
    def __init__(self, name: str, llm_instance, priority: int = 0):
        self.name = name
        self.llm = llm_instance
        self.priority = priority
        self.is_available = True
    
    def test_connection(self) -> bool:
        try:
            test_messages = [SystemMessage(content="Test"), HumanMessage(content="Hi")]
            self.llm.invoke(test_messages)
            self.is_available = True
            return True
        except Exception as e:
            logging.warning(f"Provider {self.name} unavailable: {e}")
            self.is_available = False
            return False

class Model:
    def __init__(self):
        self.providers = []
        self.current_provider = None
        self._setup_providers()
    
    def _setup_providers(self):
        # OpenRouter
        if os.getenv("OPENROUTER_API_KEY"):
            openrouter_llm = ChatOpenAI(
                openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_base="https://openrouter.ai/api/v1",
                model="deepseek/deepseek-r1-0528:free",
                temperature=0.7,
            )
            self.providers.append(ModelProvider("openrouter", openrouter_llm, priority=1))
        
        # CAILA
        if os.getenv("CAILA_API_KEY"):
            caila_llm = ChatOpenAI(
                openai_api_key=os.getenv("CAILA_API_KEY"),
                openai_api_base="https://caila.io/api/adapters/openai",
                model="just-ai/openai-proxy/gpt-4o-mini",
                temperature=0.7,
            )
            self.providers.append(ModelProvider("caila", caila_llm, priority=2))
        
        # OpenAI как fallback
        if os.getenv("OPENAI_API_KEY"):
            openai_llm = ChatOpenAI(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-3.5-turbo",
                temperature=0.7,
            )
            self.providers.append(ModelProvider("openai", openai_llm, priority=3))
        
        self.providers.sort(key=lambda x: x.priority)
        
        if not self.providers:
            raise RuntimeError("No API keys configured")
    
    def _get_working_provider(self) -> ModelProvider:
        if self.current_provider and self.current_provider.is_available:
            return self.current_provider
            
        for provider in self.providers:
            if provider.test_connection():
                self.current_provider = provider
                logging.info(f"Using provider: {provider.name}")
                return provider
        
        raise RuntimeError("All providers unavailable")
    
    def with_structured_output(self, schema):
        provider = self._get_working_provider()
        return provider.llm.with_structured_output(schema)
    
    def invoke(self, messages):
        provider = self._get_working_provider()
        try:
            return provider.llm.invoke(messages)
        except Exception as e:
            logging.error(f"Provider {provider.name} failed: {e}")
            provider.is_available = False
            self.current_provider = None
            return self._get_working_provider().llm.invoke(messages)

# Использование
model = Model()

def get_important_information(message: str):
    structured_llm = model.with_structured_output(FishingRequest)
    messages = [
        SystemMessage(content="Извлеки информацию о рыбалке из сообщения пользователя, в переменную name_place нужно записать место где человек рыбачил, например ['Река Вуокса Выборгский район'], в переменную caught_fishes ты должен записать рыб, которых пользователь поймал на этой локации, например ['щука', 'окунь'], в переменную coordinates нужно записать координаты точки где рыбак ловил рыбу, обычно это выглядит как-то так: [59.861234, 30.154855] В переменную water_space нужно записать вид водоема в котором человек рыбачил, например ['озеро'] или ['река']."),
        HumanMessage(content=message)
    ]
    result = structured_llm.invoke(messages)
    return {
        "name_place": result.name_place,
        "coordinates": result.coordinates,
        "caught_fishes": result.caught_fishes,
        "water_space": result.water_space,
    }

if __name__ == "__main__":
    print(get_important_information("Автово, щука"))