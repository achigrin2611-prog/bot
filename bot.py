import os
import logging
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher

load_dotenv()
from aiogram.filters import Command
from aiogram.types import Message

# --- Настройки ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Инициализация ---
bot = Bot(token=TOKEN)
dp = Dispatcher()


# --- Команды ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    pass


@dp.message(Command("help"))
async def cmd_help(message: Message):
    pass


@dp.message()
async def echo(message: Message):
    if message.text:
        await message.answer(f"Получено: {message.text}")


# --- Запуск ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен.")
