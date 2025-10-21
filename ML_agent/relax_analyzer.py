from enum import Enum
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from model_provider import Model


class RelaxType(Enum):
    FISHING = "рыбалка"
    CAMPING = "кемпинг"
    FISHING_AND_CAMPING = "кемпинг + рыбалка"


class RequestType(Enum):
    EXISTING_PLACES = "existing_places"
    QUERY_USERS = "query_users"


# Модели для запросов пользователей (планирование поездки)
class FishingQueryRequest(BaseModel):
    """Структура для запросов о планируемой рыбалке"""
    wish_location: Optional[List[str]] = []
    user_preferences: Optional[List[str]] = []
    user_coordinates: Optional[List[float]] = []
    caught_fishes: Optional[List[str]] = []
    water_space: Optional[List[str]] = []
    wish_price: Optional[float] = None


class CampingQueryRequest(BaseModel):
    """Структура для запросов о планируемом кемпинге"""
    wish_location: Optional[List[str]] = [None]
    user_preferences: Optional[List[str]] = []
    user_coordinates: Optional[List[float]] = []
    wish_price: Optional[float] = None




# Модели для существующих локаций (отзывы/описания мест)
class FishingExistingPlace(BaseModel):
    """Структура для информации о существующем месте рыбалки"""
    name_location: Optional[str] = None
    wish_location: Optional[str] = None
    user_preferences: Optional[List[str]] = []
    place_coordinates: Optional[List[float]] = []
    caught_fishes: Optional[List[str]] = []
    water_space: Optional[List[str]] = []
    wish_price: Optional[float] = None


class CampingExistingPlace(BaseModel):
    """Структура для информации о существующем кемпинге"""
    name_location: Optional[str] = None
    wish_location: Optional[str] = None
    user_preferences: Optional[List[str]] = []
    place_coordinates: Optional[List[float]] = []
    wish_price: Optional[float] = None


class RelaxAnalyzer:
    def __init__(self, model: Model):
        self.model = model
        
        # Контексты для рыбалки
        self.fishing_contexts = {
            RequestType.EXISTING_PLACES: """
            Извлеки информацию о рыбалке из сообщения пользователя:
            - name_location: название места рыбалки, если указано, например "Озеро Вуокса" или "Река Нева у моста"
            - wish_location: общее указание локации, например "Ленинградская область" или "под Петербургом"
            - user_preferences: КРИТИЧЕСКИ ВАЖНО - это поле НЕ ДОЛЖНО быть пустым. Извлеки ВСЕ ключевые характеристики и особенности рыболовного места из описания, которые будут полезны будущим рыбакам.
            
            Анализируй описание и выдели если встречается в тексте:
            * Условия рыбалки: глубина, течение, дно (песок/ил/камни), наличие растительности, коряг
            * Инфраструктура: наличие пирса/мостков, беседок, мест для палаток, парковки, туалетов
            * Доступность: подъезд на машине, пешая доступность, расстояние от дороги
            * Особенности локации: тихое/людное место, живописность, защита от ветра, наличие тени
            * Сервис: аренда лодок/снастей, продажа наживки, егерь, охрана
            * Условия: платная/бесплатная рыбалка, можно с ночевкой, разрешен костер
            * Сезонность: когда лучше ловить, ледовая обстановка зимой
            * Дополнительно: грибы/ягоды рядом, места для отдыха семьи, мангальные зоны
            НЕ ПРИДУМЫВАЙ НИЧЕГО НОВОГО, ЕСЛИ В ТЕКСТЕ ПРО ЭТО НЕ СКАЗАНО
            Формулируй в виде коротких информативных фраз, например:
            ['хороший подъезд', 'тихое место', 'можно с палаткой', 'песчаное дно', 'защищено от ветра', 'есть беседка']
            - place_coordinates: координаты самого места рыбалки, если указаны, например [59.861234, 30.154855]
            - caught_fishes: рыбы, которых пользователь поймал на этой локации, например ['щука', 'окунь']
            - water_space: вид водоема в котором человек рыбачил, например ['озеро'] или ['река']
            - wish_price: стоимость рыбалки на этом месте (в рублях), если указана
            """,
            
            RequestType.QUERY_USERS: """
            Извлеки информацию о планируемой рыбалке из сообщения пользователя:
            - wish_location: место, куда пользователь хочет поехать, например ['Карельский перешеек'] или ['озера Ленобласти']
            - user_preferences: общие предпочтения и пожелания пользователя, например ['хочу тихое место', 'нужна парковка', 'глубокое место', 'с пирсом', 'можно с ночевкой']
            - user_coordinates: координаты места откуда человек планирует выехать (город, район), например [59.861234, 30.154855]
            - caught_fishes: рыбы, которых пользователь хочет поймать, например ['щука', 'окунь']
            - water_space: вид водоема где человек хочет рыбачить, например ['озеро'] или ['река']
            - wish_price: желаемая цена или бюджет (в рублях), если указан
            """
        }

        # Контексты для кемпинга
        self.camping_contexts = {
            RequestType.EXISTING_PLACES: """
            Извлеки информацию о существующем кемпинге из описания локации:
            - name_location: название кемпинга/места, например "Кемпинг Ласковый берег"
            - wish_location: общее указание локации, например "Карельский перешеек" или "у озера Суходольское"
            - user_preferences: КРИТИЧЕСКИ ВАЖНО - это поле НЕ ДОЛЖНО быть пустым. Извлеки ВСЕ ключевые характеристики и преимущества места из описания, которые будут полезны будущим посетителям.
            
            Анализируй описание и выдели если встречается в тексте:
            * Инфраструктуру: наличие душа, туалетов, электричества, Wi-Fi, парковки, беседок, костровищ, мангалов
            * Расположение: близость к воде (озеро/река/море), лес, горы, удаленность от города, тишина/уединенность
            * Удобства: аренда снаряжения, магазин, кафе, баня/сауна, детская площадка
            * Особенности: живописные виды, рыбалка, грибы/ягоды, пляж, места для купания
            * Условия: можно с палатками/домиками, разрешены животные, размер территории
            * Безопасность: охрана, освещение, медпункт
            * Активности: пешие маршруты, велодорожки, водные развлечения, экскурсии
            НЕ ПРИДУМЫВАЙ НИЧЕГО НОВОГО, ЕСЛИ В ТЕКСТЕ ПРО ЭТО НЕ СКАЗАНО
            Формулируй в виде коротких информативных фраз, например:
            ['есть душ и туалеты', 'хороший подход к воде', 'оборудованные костровища', 'парковка для авто', 'тихое место в лесу', 'можно с палаткой']
            - place_coordinates: координаты самого кемпинга, если указаны, например [60.123456, 29.987654]
            - wish_price: стоимость проживания в кемпинге (в рублях), если указана
            """,
            
            RequestType.QUERY_USERS: """
            Извлеки информацию о планируемом кемпинге из сообщения пользователя:
            - wish_location: место, куда пользователь хочет поехать, например ['Карелия'] или ['побережье Финского залива']
            - user_preferences: список пожеланий пользователя, например ['нужен душ', 'хочу место с костровищем', 'желательно у воды', 'тихое место', 'можно с собакой', 'есть пляж']
            - user_coordinates: координаты места откуда человек планирует выехать, например [59.861234, 30.154855]
            - wish_price: желаемый бюджет (в рублях), если указан
            """
        }
        
    
    def _get_schema_and_context(self, relax_type: RelaxType, request_type: RequestType):
        """Возвращает нужную схему и контекст в зависимости от типа отдыха и типа запроса"""
        if request_type == RequestType.QUERY_USERS:
            # Для запросов пользователей о планируемой поездке
            if relax_type == RelaxType.FISHING:
                return FishingQueryRequest, self.fishing_contexts[request_type]
            elif relax_type == RelaxType.CAMPING:
                return CampingQueryRequest, self.camping_contexts[request_type]
        else:
            # Для существующих мест
            if relax_type == RelaxType.FISHING:
                return FishingExistingPlace, self.fishing_contexts[request_type]
            elif relax_type == RelaxType.CAMPING:
                return CampingExistingPlace, self.camping_contexts[request_type]
            
        raise ValueError(f"Неподдерживаемый тип отдыха: {relax_type}")
    
    def analyze_message(self, message: str, relax_type: RelaxType, request_type: RequestType) -> dict:
        """
        Анализирует сообщение пользователя и извлекает информацию
        
        Args:
            message: сообщение пользователя
            relax_type: тип отдыха (рыбалка, кемпинг или оба)
            request_type: тип запроса (существующие места или планируемая поездка)
            
        Returns:
            dict: словарь с извлеченной информацией
        """
        try:
            schema, context = self._get_schema_and_context(relax_type, request_type)
            structured_llm = self.model.with_structured_output(schema)
            
            messages = [
                SystemMessage(content=context),
                HumanMessage(content=message)
            ]
            
            result = structured_llm.invoke(messages)
            
            # Формируем результат в зависимости от типа запроса и отдыха
            if request_type == RequestType.EXISTING_PLACES:
                # Для существующих мест
                output = {
                    "type_of_relax": relax_type.value,
                    "name_location": result.name_location,
                    "user_preferences": result.user_preferences,
                    "place_coordinates": result.place_coordinates,
                    "wish_price": result.wish_price
                }
                
                # Добавляем специфичные для рыбалки поля
                if relax_type in [RelaxType.FISHING, RelaxType.FISHING_AND_CAMPING]:
                    output["caught_fishes"] = result.caught_fishes
                    output["water_space"] = result.water_space
            else:
                # Для запросов пользователей
                output = {
                    "type_of_relax": relax_type.value,
                    "wish_location": result.wish_location,
                    "user_preferences": result.user_preferences,
                    "user_coordinates": result.user_coordinates,
                    "wish_price": result.wish_price
                }
                
                # Добавляем специфичные для рыбалки поля
                if relax_type in RelaxType.FISHING:
                    output["caught_fishes"] = result.caught_fishes
                    output["water_space"] = result.water_space
            
            return output
            
        except Exception as e:
            logging.error(f"Failed to analyze message: {e}")
            raise
    
    def analyze_existing_place(self, message: str, relax_type: RelaxType) -> dict:
        """Анализирует сообщение о существующем месте отдыха"""
        return self.analyze_message(message, relax_type, RequestType.EXISTING_PLACES)
    
    def analyze_user_query(self, message: str, relax_type: RelaxType) -> dict:
        """Анализирует запрос пользователя о планируемом отдыхе"""
        return self.analyze_message(message, relax_type, RequestType.QUERY_USERS)


# Пример использования
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    model = Model()
    analyzer = RelaxAnalyzer(model)
    
    # Пример для рыбалки
    fishing_message = "Хочу поймать щуку и окуня на озере, выезжаю из Автово, бюджет до 5000 рублей"
    result = analyzer.analyze_user_query(fishing_message, RelaxType.FISHING)
    print("Рыбалка:", result)
    
    # Пример для кемпинга
    camping_message = "Нужно место с душем и электричеством, выезжаю из центра, бюджет 3000 рублей"
    result = analyzer.analyze_user_query(camping_message, RelaxType.CAMPING)
    print("Кемпинг:", result)
    