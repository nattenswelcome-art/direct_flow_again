"""Клавиатуры для Telegram бота."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_frequency_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора: с частотностью или без.

    Returns:
        InlineKeyboardMarkup с двумя кнопками
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 С частотностью", callback_data="with_frequency")],
            [InlineKeyboardButton(text="📝 Без частотности", callback_data="without_frequency")],
        ]
    )
    return keyboard


def get_limit_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора количества ключевых слов для экспорта.

    Returns:
        InlineKeyboardMarkup с тремя кнопками (50/100/150 слов)
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Первые 50 слов", callback_data="limit_50")],
            [InlineKeyboardButton(text="📊 Первые 100 слов", callback_data="limit_100")],
            [InlineKeyboardButton(text="📈 Первые 150 слов", callback_data="limit_150")],
        ]
    )
    return keyboard
