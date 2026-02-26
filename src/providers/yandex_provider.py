"""Провайдер для работы с Яндекс.Wordstat API."""

import asyncio
from datetime import datetime
from typing import Any

import httpx

from src.models import KeywordRow
from src.providers.base import WordstatProvider


class YandexAPIError(Exception):
    """Ошибка при работе с Яндекс API."""

    pass


class YandexWordstatProvider(WordstatProvider):
    """Провайдер для получения данных из Яндекс.Wordstat API.

    Использует асинхронный процесс:
    1. Создаёт отчёт (CreateNewWordstatReport)
    2. Ждёт готовности отчёта (GetWordstatReport с polling)
    3. Получает данные
    4. Удаляет отчёт (DeleteWordstatReport)

    Args:
        oauth_token: OAuth-токен Яндекса
        client_login: Логин клиента (если требуется)
        api_url: URL API (по умолчанию reports.api.direct.yandex.ru)
    """

    def __init__(
        self,
        oauth_token: str,
        client_login: str | None = None,
        api_url: str = "https://api.direct.yandex.ru/v4/json/",
    ):
        self.oauth_token = oauth_token
        self.client_login = client_login
        self.api_url = api_url
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        """Имя провайдера."""
        return "yandex"

    async def _get_client(self) -> httpx.AsyncClient:
        """Получить или создать HTTP клиент."""
        if self._client is None:
            headers = {
                "Authorization": f"Bearer {self.oauth_token}",
                "Accept-Language": "ru",
            }
            if self.client_login:
                headers["Client-Login"] = self.client_login

            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def _make_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Выполнить запрос к Яндекс API.

        Args:
            method: Название метода API
            params: Параметры метода

        Returns:
            Ответ API

        Raises:
            YandexAPIError: При ошибке API
        """
        client = await self._get_client()

        payload = {
            "method": method,
            "param": params,
        }

        try:
            response = await client.post(self.api_url, json=payload)
            response.raise_for_status()
            data = response.json()

            # Проверяем наличие ошибок в ответе
            if "error" in data:
                error_code = data["error"].get("error_code", "unknown")
                error_msg = data["error"].get("error_string", "Unknown error")
                raise YandexAPIError(f"API Error [{error_code}]: {error_msg}")

            return data

        except httpx.HTTPError as e:
            raise YandexAPIError(f"HTTP Error: {e}") from e

    async def _create_report(self, phrases: list[str]) -> int:
        """Создать отчёт Wordstat.

        Args:
            phrases: Список ключевых фраз

        Returns:
            ID созданного отчёта
        """
        params = {"Phrases": phrases}
        result = await self._make_request("CreateNewWordstatReport", params)

        if "data" not in result:
            raise YandexAPIError("Не удалось создать отчёт: отсутствует 'data' в ответе")

        report_id = result["data"]
        return report_id

    async def _get_report(self, report_id: int) -> dict[str, Any] | None:
        """Получить данные отчёта.

        Args:
            report_id: ID отчёта

        Returns:
            Данные отчёта или None, если отчёт ещё не готов
        """
        params = {"ReportID": report_id}
        result = await self._make_request("GetWordstatReport", params)

        if "data" not in result:
            # Отчёт ещё не готов
            return None

        return result["data"]

    async def _delete_report(self, report_id: int) -> None:
        """Удалить отчёт.

        Args:
            report_id: ID отчёта
        """
        params = {"ReportID": report_id}
        await self._make_request("DeleteWordstatReport", params)

    async def _wait_for_report(
        self, report_id: int, max_wait: int = 60, check_interval: int = 2
    ) -> dict[str, Any]:
        """Ждать готовности отчёта.

        Args:
            report_id: ID отчёта
            max_wait: Максимальное время ожидания (секунды)
            check_interval: Интервал проверки (секунды)

        Returns:
            Данные готового отчёта

        Raises:
            YandexAPIError: Если отчёт не готов за max_wait секунд
        """
        elapsed = 0

        while elapsed < max_wait:
            data = await self._get_report(report_id)

            if data is not None:
                return data

            # Ждём перед следующей проверкой
            await asyncio.sleep(check_interval)
            elapsed += check_interval

        raise YandexAPIError(f"Timeout: отчёт {report_id} не готов за {max_wait} секунд")

    async def get_keywords(
        self, phrases: list[str], with_frequency: bool = False
    ) -> list[KeywordRow]:
        """Получить ключевые слова из Яндекс.Wordstat.

        Возвращает исходные фразы + вложенные запросы из поля SearchedAlso.

        Args:
            phrases: Список исходных фраз
            with_frequency: Получать ли частотность (если False, будет None)

        Returns:
            Список KeywordRow с данными из Wordstat (исходные + вложенные запросы)
        """
        try:
            # 1. Создаём отчёт
            report_id = await self._create_report(phrases)

            # 2. Ждём готовности
            report_data = await self._wait_for_report(report_id)

            # 3. Парсим результаты
            results = []
            for item in report_data:
                # Добавляем исходную фразу
                phrase = item.get("Phrase", "")
                frequency = None
                if with_frequency and "Shows" in item:
                    frequency = item["Shows"]

                row = KeywordRow(
                    keyword=phrase,
                    frequency=frequency,
                    source=self.name,
                    created_at=datetime.now(),
                )
                results.append(row)

                # Добавляем вложенные запросы из SearchedAlso
                searched_also = item.get("SearchedAlso", [])
                for related_item in searched_also:
                    related_phrase = related_item.get("Phrase", "")
                    related_frequency = None
                    if with_frequency and "Shows" in related_item:
                        related_frequency = related_item["Shows"]

                    related_row = KeywordRow(
                        keyword=related_phrase,
                        frequency=related_frequency,
                        source=self.name,
                        created_at=datetime.now(),
                    )
                    results.append(related_row)

            # 4. Удаляем отчёт
            await self._delete_report(report_id)

            return results

        except YandexAPIError:
            raise
        except Exception as e:
            raise YandexAPIError(f"Unexpected error: {e}") from e
        finally:
            # Закрываем клиент
            if self._client:
                await self._client.aclose()
                self._client = None
