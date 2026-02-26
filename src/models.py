"""Модели данных проекта."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class KeywordRow:
    """Строка с данными о ключевом слове.

    Attributes:
        keyword: Ключевое слово
        frequency: Частотность (количество показов в месяц), None если не запрашивалась
        source: Источник данных ('mock' или 'yandex')
        created_at: Дата и время создания записи
    """

    keyword: str
    frequency: int | None
    source: str
    created_at: datetime
