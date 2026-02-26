"""Состояния для FSM (Finite State Machine)."""

from aiogram.fsm.state import State, StatesGroup


class KeywordsState(StatesGroup):
    """Состояния диалога для получения ключевых слов."""

    waiting_for_keywords = State()  # Ожидание ввода ключевых слов
    waiting_for_frequency_choice = State()  # Ожидание выбора частотности
    waiting_for_limit_choice = State()  # Ожидание выбора количества слов
