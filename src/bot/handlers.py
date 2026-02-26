"""Обработчики команд и сообщений Telegram бота."""

import asyncio

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.bot.keyboards import get_frequency_keyboard, get_limit_keyboard
from src.bot.states import KeywordsState
from src.config import config
from src.utils.excel_exporter import ExporterError, export_to_excel
from src.utils.parser import ParserError, parse_keywords

# Создаём роутер для регистрации обработчиков
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start.

    Args:
        message: Сообщение от пользователя
        state: Контекст состояния FSM
    """
    await state.clear()  # Очищаем предыдущее состояние

    welcome_text = (
        "👋 Привет! Я бот для получения ключевых слов из Яндекс.Wordstat.\n\n"
        "📝 Отправьте мне список ключевых слов:\n"
        "• Каждое слово с новой строки\n"
        "• Или через запятую\n\n"
        "Пример:\n"
        "<code>купить iPhone\n"
        "купить Samsung\n"
        "смартфон недорого</code>\n\n"
        "После этого я спрошу, нужна ли вам частотность, "
        "и отправлю Excel-файл с результатами!"
    )

    await message.answer(welcome_text, parse_mode="HTML")
    await state.set_state(KeywordsState.waiting_for_keywords)


@router.message(StateFilter(KeywordsState.waiting_for_keywords))
async def process_keywords(message: Message, state: FSMContext) -> None:
    """Обработчик ввода ключевых слов.

    Args:
        message: Сообщение с ключевыми словами
        state: Контекст состояния FSM
    """
    text = message.text

    if not text:
        await message.answer("❌ Пожалуйста, отправьте текстовое сообщение")
        return

    try:
        # Парсим ключевые слова
        keywords = parse_keywords(text, max_keywords=config.MAX_KEYWORDS)

        # Сохраняем в состояние
        await state.update_data(keywords=keywords)

        # Показываем клавиатуру выбора
        await message.answer(
            f"✅ Найдено ключевых слов: {len(keywords)}\n\n"
            "Получить частотность из Яндекс.Wordstat?",
            reply_markup=get_frequency_keyboard(),
        )

        await state.set_state(KeywordsState.waiting_for_frequency_choice)

    except ParserError as e:
        await message.answer(f"❌ Ошибка парсинга: {e}")
    except Exception as e:
        await message.answer(f"❌ Неожиданная ошибка: {e}")


@router.callback_query(
    StateFilter(KeywordsState.waiting_for_frequency_choice),
    lambda c: c.data in ["with_frequency", "without_frequency"],
)
async def process_frequency_choice(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора частотности.

    Args:
        callback: Callback от inline-кнопки
        state: Контекст состояния FSM
    """
    if not callback.message or not callback.data:
        return

    with_frequency = callback.data == "with_frequency"

    # Сохраняем выбор частотности
    await state.update_data(with_frequency=with_frequency)

    # Удаляем клавиатуру
    await callback.message.edit_reply_markup(reply_markup=None)

    # Показываем клавиатуру выбора количества слов
    await callback.message.answer(
        "📊 Сколько ключевых слов вывести в файл?",
        reply_markup=get_limit_keyboard(),
    )

    # Переходим к выбору лимита
    await state.set_state(KeywordsState.waiting_for_limit_choice)

    # Подтверждаем callback
    await callback.answer()


@router.callback_query(
    StateFilter(KeywordsState.waiting_for_limit_choice),
    lambda c: c.data in ["limit_50", "limit_100", "limit_150"],
)
async def process_limit_choice(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора количества ключевых слов.

    Args:
        callback: Callback от inline-кнопки
        state: Контекст состояния FSM
    """
    if not callback.message or not callback.data:
        return

    # Получаем лимит из callback_data
    limit_map = {
        "limit_50": 50,
        "limit_100": 100,
        "limit_150": 150,
    }
    limit = limit_map.get(callback.data, 50)

    # Удаляем клавиатуру
    await callback.message.edit_reply_markup(reply_markup=None)

    # Получаем сохранённые данные
    data = await state.get_data()
    keywords = data.get("keywords", [])
    with_frequency = data.get("with_frequency", False)

    if not keywords:
        await callback.message.answer("❌ Ошибка: ключевые слова не найдены")
        await state.clear()
        return

    # Отправляем начальный статус с прогресс-баром
    status_message = await callback.message.answer("🔄 Запуск обработки...\n\n▱▱▱▱▱▱▱▱▱▱ 0%")

    try:
        # Шаг 1: Получение данных
        await status_message.edit_text("📊 Получение данных из API...\n\n▰▰▱▱▱▱▱▱▱▱ 20%")
        provider = config.get_provider()
        results = await provider.get_keywords(keywords, with_frequency=with_frequency)

        # Шаг 2: Расширение ключевых слов
        await status_message.edit_text(
            f"🔍 Расширение ключевых слов...\n\n"
            f"Получено: {len(results)} вариантов\n\n"
            f"▰▰▰▰▱▱▱▱▱▱ 40%"
        )
        await asyncio.sleep(0.5)  # Небольшая задержка для видимости прогресса

        # Шаг 3: Ограничение результатов
        results = results[:limit]
        await status_message.edit_text(
            f"✂️ Применение лимита...\n\nКлючевых слов: {len(results)} из {limit}\n\n▰▰▰▰▰▰▱▱▱▱ 60%"
        )
        await asyncio.sleep(0.3)

        # Шаг 4: Создание Excel
        await status_message.edit_text(
            f"📄 Создание Excel файла...\n\nЗаписей: {len(results)}\n\n▰▰▰▰▰▰▰▰▱▱ 80%"
        )
        excel_file = export_to_excel(results)

        # Шаг 5: Финализация
        await status_message.edit_text(
            f"📤 Отправка файла...\n\nРазмер: {len(excel_file.getvalue())} байт\n\n▰▰▰▰▰▰▰▰▰▰ 100%"
        )
        await asyncio.sleep(0.3)

        # Готовим файл для отправки
        input_file = BufferedInputFile(file=excel_file.getvalue(), filename="keywords.xlsx")

        # Отправляем файл
        await callback.message.answer_document(
            document=input_file,
            caption=(
                f"✅ Готово!\n\n"
                f"📊 Ключевых слов: {len(results)}\n"
                f"🔧 Источник: {provider.name}\n"
                f"📝 Лимит: {limit} слов"
            ),
        )

        # Удаляем статус-сообщение
        await status_message.delete()

        # Очищаем состояние
        await state.clear()

    except ExporterError as e:
        await status_message.edit_text(f"❌ Ошибка экспорта: {e}")
        await state.clear()
    except Exception as e:
        await status_message.edit_text(f"❌ Ошибка получения данных: {e}")
        await state.clear()

    # Подтверждаем callback
    await callback.answer()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Обработчик команды /cancel для отмены текущей операции.

    Args:
        message: Сообщение от пользователя
        state: Контекст состояния FSM
    """
    await state.clear()
    await message.answer("❌ Операция отменена.\n\nОтправьте /start для начала работы.")
