import os
from typing import Set

def parse_admin_ids(env_value: str | None) -> Set[int]:
    """Парсит строку с ADMIN_ID и возвращает set[int]. Поддерживает разделители , и ; и игнорирует пробелы."""
    ids: Set[int] = set()
    if not env_value:
        return ids
    # поддерживаем запятую и точку с запятой как разделители
    for part in env_value.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            pass
    return ids

# Загружаем из окружения единожды при импорте
ADMIN_IDS: Set[int] = parse_admin_ids(os.getenv("ADMIN_ID", ""))