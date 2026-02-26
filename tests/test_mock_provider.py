"""Тесты для Mock провайдера."""

import pytest

from src.providers.mock_provider import MockWordstatProvider


@pytest.mark.asyncio
async def test_mock_provider_without_frequency():
    """Тест получения данных без частотности."""
    provider = MockWordstatProvider()
    phrases = ["test1", "test2"]

    result = await provider.get_keywords(phrases, with_frequency=False)

    assert len(result) == 2
    assert result[0].keyword == "test1"
    assert result[0].frequency is None
    assert result[0].source == "mock"


@pytest.mark.asyncio
async def test_mock_provider_with_frequency():
    """Тест получения данных с частотностью."""
    provider = MockWordstatProvider()
    phrases = ["test"]

    result = await provider.get_keywords(phrases, with_frequency=True)

    assert len(result) == 1
    assert result[0].frequency is not None
    assert isinstance(result[0].frequency, int)
    assert 100 <= result[0].frequency <= 10000


@pytest.mark.asyncio
async def test_mock_provider_deterministic():
    """Тест детерминированности (одна фраза → одна частота)."""
    provider = MockWordstatProvider()
    phrase = ["купить iPhone"]

    result1 = await provider.get_keywords(phrase, with_frequency=True)
    result2 = await provider.get_keywords(phrase, with_frequency=True)

    assert result1[0].frequency == result2[0].frequency


@pytest.mark.asyncio
async def test_mock_provider_empty_list():
    """Тест с пустым списком фраз."""
    provider = MockWordstatProvider()

    result = await provider.get_keywords([], with_frequency=False)

    assert result == []


@pytest.mark.asyncio
async def test_mock_provider_name():
    """Тест имени провайдера."""
    provider = MockWordstatProvider()
    assert provider.name == "mock"
