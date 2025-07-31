from langchain_openai import ChatOpenAI
from enum import Enum
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

class RequestType(Enum):
    EXISTING_PLACES = "existing_places"
    QUERY_USERS = "query_users"

load_dotenv()

class ModelProvider:
    def __init__(self, name: str, llm_instance, priority: int = 0):
        self.name = name
        self.llm = llm_instance
        self.priority = priority
        self.is_available = True
        self.failure_count = 0
        self.max_failures = 1
    
    def test_connection(self) -> bool:
        try:
            test_messages = [SystemMessage(content="Test"), HumanMessage(content="Hi")]
            response = self.llm.invoke(test_messages)
            self.reset_failures()  # Сбрасываем ошибки при успешном подключении
            return True
        except Exception as e:
            logging.warning(f"Provider {self.name} test failed: {e}")
            self.mark_failed()
            return False
    
    def mark_failed(self):
        """Отмечает провайдера как неуспешного"""
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            self.is_available = False
            logging.error(f"Provider {self.name} marked as unavailable after {self.failure_count} failures")
        else:
            logging.warning(f"Provider {self.name} failed ({self.failure_count}/{self.max_failures})")
    
    def reset_failures(self):
        """Сбрасывает счетчик ошибок и помечает провайдера как доступного"""
        self.failure_count = 0
        self.is_available = True
        logging.info(f"Provider {self.name} restored")

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
        """Получает рабочего провайдера, тестируя их по приоритету"""
        # Сначала проверяем текущего провайдера
        if self.current_provider and self.current_provider.is_available:
            return self.current_provider
            
        # Если текущий не работает, ищем рабочего среди доступных
        for provider in self.providers:
            if provider.is_available:
                self.current_provider = provider
                logging.info(f"Using provider: {provider.name}")
                return provider
        
        # Если нет доступных, пробуем переподключиться
        for provider in self.providers:
            if provider.test_connection():
                self.current_provider = provider
                logging.info(f"Reconnected to provider: {provider.name}")
                return provider
        
        raise RuntimeError("All providers unavailable")
    
    def _try_with_fallback(self, operation_func, *args, **kwargs):
        """Выполняет операцию с автоматическим переключением провайдеров при ошибке"""
        tried_providers = set()
        last_error = None
        
        while len(tried_providers) < len(self.providers):
            try:
                # Получаем доступного провайдера
                available_providers = [p for p in self.providers if p.name not in tried_providers]
                if not available_providers:
                    break
                    
                # Выбираем провайдера с наивысшим приоритетом среди доступных
                provider = min(available_providers, key=lambda x: x.priority)
                tried_providers.add(provider.name)
                
                # Если провайдер помечен как недоступный, пробуем переподключиться
                if not provider.is_available:
                    if not provider.test_connection():
                        continue
                
                logging.info(f"Trying provider: {provider.name}")
                result = operation_func(provider, *args, **kwargs)
                
                # Успешно выполнили операцию
                self.current_provider = provider
                return result
                
            except Exception as e:
                last_error = e
                logging.error(f"Provider {provider.name} failed: {e}")
                provider.mark_failed()
                
                # Сбрасываем текущего провайдера, если он упал
                if self.current_provider == provider:
                    self.current_provider = None
                
                continue
        
        # Если все провайдеры не работают
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
    
    def get_provider_status(self):
        """Возвращает статус всех провайдеров"""
        return {
            provider.name: {
                "available": provider.is_available,
                "failures": provider.failure_count,
                "priority": provider.priority,
                "is_current": provider == self.current_provider
            }
            for provider in self.providers
        }
    
    def with_structured_output(self, schema):
        """Создает structured output с автоматическим переключением провайдеров"""
        def create_structured_output(provider, schema):
            return provider.llm.with_structured_output(schema)
        
        return StructuredOutputWrapper(self, schema, create_structured_output)
    
    def invoke(self, messages):
        """Выполняет запрос с автоматическим переключением провайдеров"""
        def invoke_operation(provider, messages):
            return provider.llm.invoke(messages)
        
        return self._try_with_fallback(invoke_operation, messages)


class StructuredOutputWrapper:
    """Обертка для structured output с поддержкой переключения провайдеров"""
    
    def __init__(self, model, schema, create_func):
        self.model = model
        self.schema = schema
        self.create_func = create_func
    
    def invoke(self, messages):
        """Выполняет structured output запрос с автоматическим переключением"""
        def structured_invoke(provider, messages):
            structured_llm = self.create_func(provider, self.schema)
            return structured_llm.invoke(messages)
        
        return self.model._try_with_fallback(structured_invoke, messages)


class FishingAnalyzer:
    def __init__(self, model):
        self.model = model
        
        # Контексты для разных типов запросов
        self.contexts = {
            RequestType.EXISTING_PLACES: """
            Извлеки информацию о рыбалке из сообщения пользователя:
            - name_place: место где человек рыбачил, например ['Река Вуокса Выборгский район']
            - caught_fishes: рыб, которых пользователь поймал на этой локации, например ['щука', 'окунь']
            - coordinates: координаты точки где рыбак ловил рыбу, например [59.861234, 30.154855]
            - water_space: вид водоема в котором человек рыбачил, например ['озеро'] или ['река']
            """,
            
            RequestType.QUERY_USERS: """
            Извлеки информацию о планируемой рыбалке из сообщения пользователя:
            - name_place: место откуда человек хочет поехать на рыбалку (город, район, адрес), например ['станция метро Автово']
            - caught_fishes: рыб, которых пользователь хочет поймать, например ['щука', 'окунь']
            - coordinates: если указаны координаты желаемого места рыбалки, например [59.861234, 30.154855]
            - water_space: вид водоема где человек хочет рыбачить, например ['озеро'] или ['река']
            """
        }
    
    def get_important_information(self, message: str, request_type: RequestType) -> dict:
        """
        Извлекает информацию о рыбалке из сообщения пользователя
        
        Args:
            message: сообщение пользователя
            request_type: тип запроса (существующие места или планируемая поездка)
            
        Returns:
            dict: словарь с извлеченной информацией
        """
        if request_type not in self.contexts:
            raise ValueError(f"Неподдерживаемый тип запроса: {request_type}")
        
        try:
            structured_llm = self.model.with_structured_output(FishingRequest)
            
            messages = [
                SystemMessage(content=self.contexts[request_type]),
                HumanMessage(content=message)
            ]
            
            result = structured_llm.invoke(messages)
            
            return {
                "name_place": result.name_place,
                "coordinates": result.coordinates,
                "caught_fishes": result.caught_fishes,
                "water_space": result.water_space,
            }
            
        except Exception as e:
            logging.error(f"Failed to analyze message: {e}")
            raise
    
    def analyze_existing_places(self, message: str) -> dict:
        """Анализирует сообщение о существующих местах рыбалки"""
        return self.get_important_information(message, RequestType.EXISTING_PLACES)
    
    def analyze_query_users(self, message: str) -> dict:
        """Анализирует запрос пользователя о планируемой рыбалке"""
        return self.get_important_information(message, RequestType.QUERY_USERS)

# Использование с улучшенным логированием
if __name__ == "__main__":
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        model = Model()
        
        # Показываем статус провайдеров
        print("=== Provider Status ===")
        for name, status in model.get_provider_status().items():
            print(f"{name}: available={status['available']}, failures={status['failures']}, priority={status['priority']}")
        print("=====================")
        
        analyzer = FishingAnalyzer(model)
        
        result1 = analyzer.analyze_existing_places("Вчера рыбачил на Вуоксе, поймал щуку и окуня")
        print("Результат анализа:", result1)
        
        # Показываем финальный статус провайдеров
        print("\n=== Final Provider Status ===")
        for name, status in model.get_provider_status().items():
            print(f"{name}: available={status['available']}, failures={status['failures']}, current={status['is_current']}")
        
        # Можно также попробовать второй запрос
        result2 = analyzer.analyze_query_users("Хочу поехать на рыбалку из Автово, ловить щуку на озере")
        print("Результат запроса:", result2)
        
    except Exception as e:
        logging.error(f"Application error: {e}")
        print(f"Ошибка: {e}")
        
        # Показываем статус провайдеров при ошибке
        if 'model' in locals():
            print("\n=== Provider Status on Error ===")
            for name, status in model.get_provider_status().items():
                print(f"{name}: available={status['available']}, failures={status['failures']}")