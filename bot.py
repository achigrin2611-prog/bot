import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiohttp import web

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Отправь мне картинку, и я скажу её ID.")


@dp.message()
async def get_id(message: types.Message):
    if message.photo:
        file_id = message.photo[-1].file_id
        logger.info(f"=== ВАШ FILE_ID: {file_id} ===")
        await message.answer("ID получен! Смотри логи на Render.")
    else:
        await message.answer("Это не картинка. Отправь фото.")


async def handle_ping(request):
    return web.Response(text="Bot is running!")


async def main():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Сервер запущен на порту {port}")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())