"""Обработчики команд и сообщений Telegram бота."""

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.bot.keyboards import get_frequency_keyboard
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

    # Удаляем клавиатуру
    await callback.message.edit_reply_markup(reply_markup=None)

    # Получаем сохранённые ключевые слова
    data = await state.get_data()
    keywords = data.get("keywords", [])

    if not keywords:
        await callback.message.answer("❌ Ошибка: ключевые слова не найдены")
        await state.clear()
        return

    # Отправляем статус
    status_message = await callback.message.answer(
        "⏳ Обрабатываю запрос...\nЭто может занять несколько секунд."
    )

    try:
        # Получаем провайдер и данные
        provider = config.get_provider()
        results = await provider.get_keywords(keywords, with_frequency=with_frequency)

        # Создаём Excel
        excel_file = export_to_excel(results)

        # Готовим файл для отправки
        input_file = BufferedInputFile(file=excel_file.getvalue(), filename="keywords.xlsx")

        # Отправляем файл
        await callback.message.answer_document(
            document=input_file,
            caption=f"✅ Готово!\n\n📊 Ключевых слов: {len(results)}\n🔧 Источник: {provider.name}",
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
