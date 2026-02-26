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
    - Расширяет ключевые слова дополнительными вариантами
    """

    # Шаблоны для расширения ключевых слов
    EXPANSIONS = [
        "",  # Исходный ключ
        "{} купить",
        "{} цена",
        "{} недорого",
        "{} отзывы",
        "{} характеристики",
        "купить {}",
        "{} в москве",
        "{} онлайн",
        "{} интернет магазин",
        "{} доставка",
        "{} как выбрать",
        "{} сравнение",
        "{} лучшие",
        "{} топ",
        "{} рейтинг",
    ]

    @property
    def name(self) -> str:
        """Имя провайдера."""
        return "mock"

    def _generate_expanded_keywords(self, phrase: str, count: int = 50) -> list[str]:
        """Генерирует расширенные варианты ключевого слова.

        Args:
            phrase: Исходное ключевое слово
            count: Количество вариантов для генерации

        Returns:
            Список расширенных ключевых слов
        """
        expanded = []

        # Добавляем исходный ключ
        expanded.append(phrase)

        # Генерируем варианты по шаблонам
        for template in self.EXPANSIONS[1:]:
            if len(expanded) >= count:
                break
            keyword = template.format(phrase)
            expanded.append(keyword)

        # Если нужно еще больше вариантов, генерируем с числами
        if len(expanded) < count:
            numbers = [
                "2024",
                "2025",
                "pro",
                "max",
                "mini",
                "lite",
                "plus",
                "premium",
            ]
            for num in numbers:
                if len(expanded) >= count:
                    break
                expanded.append(f"{phrase} {num}")

        return expanded[:count]

    async def get_keywords(
        self, phrases: list[str], with_frequency: bool = False
    ) -> list[KeywordRow]:
        """Возвращает mock-данные для ключевых слов с расширением.

        Args:
            phrases: Список ключевых слов
            with_frequency: Нужно ли генерировать частотность

        Returns:
            Список KeywordRow с mock-данными (расширенный)
        """
        results = []

        # Для каждой фразы генерируем ~50 вариантов
        for phrase in phrases:
            expanded_keywords = self._generate_expanded_keywords(phrase, count=50)

            for keyword in expanded_keywords:
                # Генерируем "стабильную" частотность на основе хеша фразы
                frequency = None
                if with_frequency:
                    # Используем хеш для генерации числа от 100 до 10000
                    hash_value = int(hashlib.md5(keyword.encode()).hexdigest(), 16)
                    frequency = 100 + (hash_value % 9900)

                row = KeywordRow(
                    keyword=keyword,
                    frequency=frequency,
                    source=self.name,
                    created_at=datetime.now(),
                )
                results.append(row)

        return results
