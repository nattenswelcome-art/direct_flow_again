"""Mock-провайдер для тестирования и разработки без реального API."""

import hashlib
from datetime import datetime

from src.models import KeywordRow
from src.providers.base import WordstatProvider


class MockWordstatProvider(WordstatProvider):
    """Тестовый провайдер, который возвращает предсказуемые данные.

    Не требует токенов API, работает всегда. Используется для:
    - Разработки бота без доступа к Яндекс API
    - Unit-тестов (не зависят от сети)
    - Демонстрации функционала

    Генерирует "правдоподобные" данные:
    - Частотность зависит от длины ключевого слова (детерминированно)
    - Каждый ключ всегда даёт одинаковую частотность
    """

    @property
    def name(self) -> str:
        """Имя провайдера."""
        return "mock"

    async def get_keywords(
        self, phrases: list[str], with_frequency: bool = False
    ) -> list[KeywordRow]:
        """Возвращает mock-данные для ключевых слов.

        Args:
            phrases: Список ключевых слов
            with_frequency: Нужно ли генерировать частотность

        Returns:
            Список KeywordRow с mock-данными
        """
        results = []

        for phrase in phrases:
            # Генерируем "стабильную" частотность на основе хеша фразы
            # (одна и та же фраза всегда даст одинаковую частотность)
            frequency = None
            if with_frequency:
                # Используем хеш для генерации числа от 100 до 10000
                hash_value = int(hashlib.md5(phrase.encode()).hexdigest(), 16)
                frequency = 100 + (hash_value % 9900)

            row = KeywordRow(
                keyword=phrase,
                frequency=frequency,
                source=self.name,
                created_at=datetime.now(),
            )
            results.append(row)

        return results
