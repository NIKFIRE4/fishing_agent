from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


model = SentenceTransformer('all-MiniLM-L6-v2')  
def get_similarity(name1, name2):
    try:
        embeddings = model.encode([name1, name2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        if similarity >=0.94:
            return True
        else:
            return False
    except:
        return {"Ошибка при сравнении имен"}



print(get_similarity("Выборгский залив, бухта Тихая, Матросово", "тихая бухта,у матросово, залив Выборгский,"))