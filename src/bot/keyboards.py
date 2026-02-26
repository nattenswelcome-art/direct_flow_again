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
