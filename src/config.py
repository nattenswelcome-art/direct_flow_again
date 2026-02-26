"""Конфигурация проекта и загрузка переменных окружения."""

import os

from dotenv import load_dotenv

from src.providers.base import WordstatProvider
from src.providers.mock_provider import MockWordstatProvider
from src.providers.yandex_provider import YandexWordstatProvider

# Загружаем переменные из .env файла
load_dotenv()


class Config:
    """Конфигурация приложения."""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Яндекс API
    YANDEX_OAUTH_TOKEN: str = os.getenv("YANDEX_OAUTH_TOKEN", "")
    YANDEX_CLIENT_LOGIN: str | None = os.getenv("YANDEX_CLIENT_LOGIN")

    # Настройки провайдера
    MAX_KEYWORDS: int = int(os.getenv("MAX_KEYWORDS", "200"))

    @classmethod
    def get_provider(cls) -> WordstatProvider:
        """Получить провайдер данных (автоматический выбор).

        Логика выбора:
        - Если есть YANDEX_OAUTH_TOKEN → YandexWordstatProvider
        - Иначе → MockWordstatProvider

        Returns:
            Экземпляр провайдера
        """
        if cls.YANDEX_OAUTH_TOKEN:
            print("📊 Используется Yandex Wordstat API")
            return YandexWordstatProvider(
                oauth_token=cls.YANDEX_OAUTH_TOKEN,
                client_login=cls.YANDEX_CLIENT_LOGIN,
            )
        else:
            print("🎭 Используется Mock Provider (тестовые данные)")
            return MockWordstatProvider()

    @classmethod
    def validate(cls) -> None:
        """Проверить обязательные переменные окружения.

        Raises:
            ValueError: Если не хватает обязательных переменных
        """
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN не задан! Создайте файл .env и добавьте токен бота."
            )


# Глобальный экземпляр конфигурации
config = Config()
