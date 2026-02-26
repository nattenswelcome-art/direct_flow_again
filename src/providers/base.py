"""Базовый интерфейс для провайдеров данных о ключевых словах."""

from abc import ABC, abstractmethod

from src.models import KeywordRow


class WordstatProvider(ABC):
    """Абстрактный базовый класс для провайдеров данных о ключевых словах.

    Все провайдеры (Mock, Yandex) должны наследоваться от этого класса
    и реализовать метод get_keywords().
    """

    @abstractmethod
    async def get_keywords(
        self, phrases: list[str], with_frequency: bool = False
    ) -> list[KeywordRow]:
        """Получить данные о ключевых словах.

        Args:
            phrases: Список исходных фраз для анализа
            with_frequency: Нужно ли получать частотность

        Returns:
            Список объектов KeywordRow с данными о ключевых словах

        Raises:
            Exception: При ошибках получения данных
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Имя провайдера (для логов и отображения)."""
        pass
