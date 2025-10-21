"""
Unified encoding service for text similarity and semantic embeddings.
Использует разные модели для разных задач:
- all-MiniLM-L6-v2: для быстрого сравнения названий мест
- paraphrase-multilingual-MiniLM-L12-v2: для семантического поиска по предпочтениям
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Union, Optional


# Модель для сравнения названий (быстрая, для коротких текстов)
_name_model = None

# Модель для семантического поиска (мультиязычная, для описаний)
_semantic_model = None


def _get_name_model() -> SentenceTransformer:
    """Ленивая инициализация модели для сравнения названий."""
    global _name_model
    if _name_model is None:
        _name_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _name_model


def _get_semantic_model() -> SentenceTransformer:
    """Ленивая инициализация модели для семантического поиска."""
    global _semantic_model
    if _semantic_model is None:
        _semantic_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _semantic_model


# ==================== ФУНКЦИИ ДЛЯ СРАВНЕНИЯ НАЗВАНИЙ ====================

def get_similarity(name1: str, name2: str, threshold: float = 0.94) -> bool:
    """
    Сравнивает два названия мест и определяет, являются ли они одним и тем же местом.
    Использует быструю модель all-MiniLM-L6-v2.
    
    Args:
        name1: Первое название
        name2: Второе название
        threshold: Порог сходства (по умолчанию 0.94)
        
    Returns:
        True если названия совпадают (similarity >= threshold), иначе False
        
    Example:
        >>> get_similarity("Выборгский залив, бухта Тихая", "тихая бухта, залив Выборгский")
        True
    """
    try:
        model = _get_name_model()
        embeddings = model.encode([name1, name2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return similarity >= threshold
    except Exception as e:
        print(f"Ошибка при сравнении имен: {e}")
        return False

def get_one_name_embedding(name1: str) -> list[float]:
    try:
        model = _get_name_model()
        embeddings = model.encode(name1)
        # Явно конвертируем каждый элемент в float
        return [float(x) for x in embeddings]
    except Exception as e:
        print(f"Ошибка при вычислении сходства: {e}")
        return []
def get_name_similarity_score(name1: str, name2: str) -> float:
    """
    Возвращает числовое значение сходства между названиями (от 0 до 1).
    
    Args:
        name1: Первое название
        name2: Второе название
        
    Returns:
        Значение сходства от 0 до 1
    """
    try:
        model = _get_name_model()
        embeddings = model.encode([name1, name2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)
    except Exception as e:
        print(f"Ошибка при вычислении сходства: {e}")
        return 0.0


# ==================== ФУНКЦИИ ДЛЯ СЕМАНТИЧЕСКОГО ПОИСКА ====================

def create_semantic_embedding(text: Union[str, List[str]]) -> List[float]:
    """
    Создает векторное представление для семантического поиска.
    Использует мультиязычную модель для лучшего понимания русского языка.
    
    Args:
        text: Строка или список строк для преобразования в вектор
        
    Returns:
        Список чисел (вектор) размерности 384
        
    Example:
        >>> prefs = ["тихое место", "есть причал", "мало людей"]
        >>> embedding = create_semantic_embedding(prefs)
        >>> len(embedding)
        384
    """
    try:
        model = _get_semantic_model()
        
        # Если список строк - объединяем в один текст
        if isinstance(text, list):
            text = ". ".join(text)
        
        # Создаем embedding
        embedding = model.encode(text, convert_to_numpy=True)
        
        # Преобразуем numpy array в list для JSON
        return embedding.tolist()
    except Exception as e:
        print(f"Ошибка при создании embedding: {e}")
        return [0.0] * 384  # Возвращаем нулевой вектор в случае ошибки


def calculate_semantic_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Вычисляет косинусное сходство между двумя векторами.
    
    Args:
        embedding1: Первый вектор
        embedding2: Второй вектор
        
    Returns:
        Значение сходства от 0 до 1 (1 = полностью похожи, 0 = совершенно разные)
    """
    try:
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Косинусное сходство
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        # Нормализуем в диапазон [0, 1]
        return float((similarity + 1) / 2)
    except Exception as e:
        print(f"Ошибка при вычислении сходства: {e}")
        return 0.0


def find_most_similar_places(
    query_embedding: List[float], 
    places: List[dict],
    embedding_key: str = "preferences_embedding",
    top_k: int = 5,
    min_similarity: Optional[float] = None
) -> List[tuple]:
    """
    Находит наиболее похожие места из списка на основе семантического сходства.
    
    Args:
        query_embedding: Вектор запроса пользователя
        places: Список мест с embeddings
        embedding_key: Ключ в словаре, где хранится embedding
        top_k: Максимальное количество результатов
        min_similarity: Минимальный порог сходства (опционально)
        
    Returns:
        Список кортежей (место, similarity_score) отсортированный по убыванию similarity
        
    Example:
        >>> user_prefs = ["тихое место", "хорошая рыбалка"]
        >>> query_emb = create_semantic_embedding(user_prefs)
        >>> similar = find_most_similar_places(query_emb, all_places, top_k=3)
        >>> for place, score in similar:
        ...     print(f"{place['name']}: {score:.2f}")
    """
    results = []
    
    for place in places:
        place_embedding = place.get(embedding_key)
        
        if not place_embedding:
            continue
        
        similarity = calculate_semantic_similarity(query_embedding, place_embedding)
        
        # Фильтруем по минимальному порогу, если указан
        if min_similarity is not None and similarity < min_similarity:
            continue
            
        results.append((place, similarity))
    
    # Сортируем по убыванию similarity
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:top_k]


def compare_preferences(
    user_preferences: List[str], 
    place_preferences: List[str]
) -> float:
    """
    Быстрое сравнение предпочтений пользователя с предпочтениями места.
    Создает embeddings на лету и возвращает оценку сходства.
    
    Args:
        user_preferences: Список предпочтений пользователя
        place_preferences: Список предпочтений места
        
    Returns:
        Оценка сходства от 0 до 1
        
    Example:
        >>> user = ["тихое место", "хорошая рыбалка"]
        >>> place = ["спокойная обстановка", "отличный клёв"]
        >>> score = compare_preferences(user, place)
        >>> print(f"Сходство: {score:.2f}")
    """
    user_emb = create_semantic_embedding(user_preferences)
    place_emb = create_semantic_embedding(place_preferences)
    return calculate_semantic_similarity(user_emb, place_emb)


