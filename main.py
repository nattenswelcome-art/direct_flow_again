"""Главный файл для запуска Telegram бота."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.handlers import router
from src.config import config


async def main() -> None:
    """Главная функция для запуска бота."""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Проверка конфигурации
    try:
        config.validate()
    except ValueError as e:
        logging.error(f"❌ Ошибка конфигурации: {e}")
        return

    # Создаём бота и диспетчер
    bot = Bot(
        token=config.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Storage для FSM (хранение состояний пользователей)
    storage = MemoryStorage()

    # Диспетчер для обработки сообщений
    dp = Dispatcher(storage=storage)

    # Регистрируем роутер с обработчиками
    dp.include_router(router)

    # Информация о провайдере
    provider = config.get_provider()
    logging.info(f"🚀 Бот запускается с провайдером: {provider.name}")

    # Запускаем бота
    try:
        logging.info("✅ Бот успешно запущен!")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
