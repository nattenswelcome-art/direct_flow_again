"""Парсинг входного текста от пользователя в список ключевых слов."""

import re


class ParserError(Exception):
    """Ошибка при парсинге ключевых слов."""

    pass


def parse_keywords(text: str, max_keywords: int = 200) -> list[str]:
    """Парсит текст и возвращает список уникальных ключевых слов.

    Поддерживаемые форматы:
    - Каждое слово с новой строки
    - Через запятую
    - Смешанный формат

    Args:
        text: Исходный текст от пользователя
        max_keywords: Максимальное количество ключевых слов

    Returns:
        Список уникальных ключевых слов (в том же порядке, в каком встречались)

    Raises:
        ParserError: Если текст пустой или нет ни одного ключевого слова

    Examples:
        >>> parse_keywords("купить телефон\\nкупить iPhone")
        ['купить телефон', 'купить iPhone']

        >>> parse_keywords("слово1, слово2, слово3")
        ['слово1', 'слово2', 'слово3']
    """
    if not text or not text.strip():
        raise ParserError("Текст не может быть пустым")

    # Разделяем по переносам строк и запятым
    # Сначала разбиваем по переносам строк
    lines = text.split("\n")

    keywords = []
    seen = set()  # Для отслеживания дубликатов

    for line in lines:
        # Разбиваем каждую строку по запятым
        parts = re.split(r",|;", line)

        for part in parts:
            # Убираем пробелы по краям
            keyword = part.strip()

            # Пропускаем пустые строки
            if not keyword:
                continue

            # Нормализуем пробелы внутри (несколько пробелов → один)
            keyword = " ".join(keyword.split())

            # Добавляем только если не встречали ранее
            if keyword.lower() not in seen:
                keywords.append(keyword)
                seen.add(keyword.lower())

    # Проверяем, что получили хотя бы одно ключевое слово
    if not keywords:
        raise ParserError("Не найдено ни одного ключевого слова в тексте")

    # Проверяем лимит
    if len(keywords) > max_keywords:
        raise ParserError(f"Слишком много ключевых слов: {len(keywords)}. Максимум: {max_keywords}")

    return keywords
