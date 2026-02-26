"""Тесты для модуля экспорта в Excel."""

from datetime import datetime
from io import BytesIO

import pytest

from src.models import KeywordRow
from src.utils.excel_exporter import ExporterError, export_to_excel


def test_export_to_excel_success():
    """Тест успешного экспорта в Excel."""
    rows = [
        KeywordRow("купить iPhone", 1000, "mock", datetime.now()),
        KeywordRow("купить Samsung", 500, "mock", datetime.now()),
    ]

    result = export_to_excel(rows)

    assert isinstance(result, BytesIO)
    assert len(result.getvalue()) > 0  # Файл не пустой


def test_export_to_excel_with_none_frequency():
    """Тест экспорта с частотностью = None."""
    rows = [
        KeywordRow("test", None, "mock", datetime.now()),
    ]

    result = export_to_excel(rows)

    assert isinstance(result, BytesIO)
    assert len(result.getvalue()) > 0


def test_export_to_excel_empty_list():
    """Тест ошибки при пустом списке."""
    with pytest.raises(ExporterError, match="Список ключевых слов пустой"):
        export_to_excel([])


def test_export_to_excel_file_readable():
    """Тест что файл можно прочитать pandas."""
    import pandas as pd

    rows = [
        KeywordRow("test1", 100, "mock", datetime.now()),
        KeywordRow("test2", 200, "yandex", datetime.now()),
    ]

    excel_file = export_to_excel(rows)
    excel_file.seek(0)  # Вернуться в начало файла

    # Читаем Excel обратно
    df = pd.read_excel(excel_file, engine="openpyxl")

    assert len(df) == 2
    assert list(df["Ключевое слово"]) == ["test1", "test2"]
    assert df["Источник"].tolist() == ["mock", "yandex"]
