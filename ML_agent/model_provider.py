from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
import logging
from dotenv import load_dotenv

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
            self.reset_failures()
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
        if self.current_provider and self.current_provider.is_available:
            return self.current_provider
            
        for provider in self.providers:
            if provider.is_available:
                self.current_provider = provider
                logging.info(f"Using provider: {provider.name}")
                return provider
        
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
                available_providers = [p for p in self.providers if p.name not in tried_providers]
                if not available_providers:
                    break
                    
                provider = min(available_providers, key=lambda x: x.priority)
                tried_providers.add(provider.name)
                
                if not provider.is_available:
                    if not provider.test_connection():
                        continue
                
                logging.info(f"Trying provider: {provider.name}")
                result = operation_func(provider, *args, **kwargs)
                
                self.current_provider = provider
                return result
                
            except Exception as e:
                last_error = e
                logging.error(f"Provider {provider.name} failed: {e}")
                provider.mark_failed()
                
                if self.current_provider == provider:
                    self.current_provider = None
                
                continue
        
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