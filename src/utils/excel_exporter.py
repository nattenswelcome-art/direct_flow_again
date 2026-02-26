"""Экспорт данных о ключевых словах в Excel (.xlsx)."""

from io import BytesIO

import pandas as pd

from src.models import KeywordRow


class ExporterError(Exception):
    """Ошибка при экспорте данных в Excel."""

    pass


def export_to_excel(keywords: list[KeywordRow], filename: str = "keywords.xlsx") -> BytesIO:
    """Экспортирует список ключевых слов в Excel файл.

    Args:
        keywords: Список объектов KeywordRow
        filename: Имя файла (используется только для метаданных)

    Returns:
        BytesIO объект с Excel файлом (в памяти, не на диске)

    Raises:
        ExporterError: Если список пустой или ошибка при создании файла

    Examples:
        >>> from datetime import datetime
        >>> from src.models import KeywordRow
        >>> rows = [
        ...     KeywordRow("купить iPhone", 1000, "mock", datetime.now()),
        ...     KeywordRow("купить Samsung", None, "mock", datetime.now())
        ... ]
        >>> excel_file = export_to_excel(rows)
        >>> print(type(excel_file))
        <class '_io.BytesIO'>
    """
    if not keywords:
        raise ExporterError("Список ключевых слов пустой")

    # Преобразуем список KeywordRow в список словарей для pandas
    data = []
    for kw in keywords:
        row = {
            "Ключевое слово": kw.keyword,
            "Частотность": kw.frequency if kw.frequency is not None else "—",
            "Источник": kw.source,
            "Дата создания": kw.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        data.append(row)

    try:
        # Создаем DataFrame (таблицу)
        df = pd.DataFrame(data)

        # Создаем BytesIO объект (виртуальный файл в памяти)
        output = BytesIO()

        # Записываем Excel в память с помощью openpyxl
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Ключевые слова")

            # Получаем доступ к worksheet для форматирования
            worksheet = writer.sheets["Ключевые слова"]

            # Автоматическая ширина колонок
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except Exception:
                        pass

                adjusted_width = min(max_length + 2, 50)  # Максимум 50 символов
                worksheet.column_dimensions[column_letter].width = adjusted_width

        # Возвращаем указатель в начало файла
        output.seek(0)
        return output

    except Exception as e:
        raise ExporterError(f"Ошибка при создании Excel файла: {e}") from e
