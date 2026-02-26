"""Тесты для модуля парсинга ключевых слов."""

import pytest

from src.utils.parser import ParserError, parse_keywords


def test_parse_keywords_newlines():
    """Тест парсинга ключевых слов разделённых переносами строк."""
    text = "купить iPhone\nкупить Samsung\nсмартфон"
    result = parse_keywords(text)
    assert result == ["купить iPhone", "купить Samsung", "смартфон"]


def test_parse_keywords_commas():
    """Тест парсинга ключевых слов разделённых запятыми."""
    text = "слово1, слово2, слово3"
    result = parse_keywords(text)
    assert result == ["слово1", "слово2", "слово3"]


def test_parse_keywords_mixed():
    """Тест парсинга со смешанным форматом."""
    text = "слово1, слово2\nслово3; слово4"
    result = parse_keywords(text)
    assert result == ["слово1", "слово2", "слово3", "слово4"]


def test_parse_keywords_removes_duplicates():
    """Тест удаления дубликатов (case-insensitive)."""
    text = "test\nTest\nTEST\ntest2"
    result = parse_keywords(text)
    assert result == ["test", "test2"]


def test_parse_keywords_strips_whitespace():
    """Тест удаления пробелов по краям."""
    text = "  слово1  ,  слово2  \n  слово3  "
    result = parse_keywords(text)
    assert result == ["слово1", "слово2", "слово3"]


def test_parse_keywords_normalizes_spaces():
    """Тест нормализации пробелов внутри фраз."""
    text = "купить    iPhone"
    result = parse_keywords(text)
    assert result == ["купить iPhone"]


def test_parse_keywords_empty_text():
    """Тест ошибки при пустом тексте."""
    with pytest.raises(ParserError, match="Текст не может быть пустым"):
        parse_keywords("")


def test_parse_keywords_only_whitespace():
    """Тест ошибки при тексте из одних пробелов."""
    with pytest.raises(ParserError, match="Текст не может быть пустым"):
        parse_keywords("   \n  \n  ")


def test_parse_keywords_no_valid_keywords():
    """Тест ошибки когда нет ни одного валидного ключевого слова."""
    with pytest.raises(ParserError, match="Не найдено ни одного ключевого слова"):
        parse_keywords(",,,\n;;;")


def test_parse_keywords_max_limit():
    """Тест проверки лимита ключевых слов."""
    # Создаём 201 ключевое слово
    keywords = "\n".join([f"keyword{i}" for i in range(201)])
    with pytest.raises(ParserError, match="Слишком много ключевых слов"):
        parse_keywords(keywords, max_keywords=200)


def test_parse_keywords_custom_max_limit():
    """Тест с пользовательским лимитом."""
    text = "слово1, слово2, слово3"
    with pytest.raises(ParserError, match="Слишком много ключевых слов"):
        parse_keywords(text, max_keywords=2)
