import os
import logging
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ===== ГЛАВНОЕ МЕНЮ =====
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📁 Каталог", callback_data="catalog"))
    builder.row(InlineKeyboardButton(text="🎁 Подобрать подарок", callback_data="gift"))
    builder.row(InlineKeyboardButton(text="✏️ Индивидуальный заказ", callback_data="custom"))
    builder.row(
        InlineKeyboardButton(text="💰 Цены и доставка", callback_data="prices"),
        InlineKeyboardButton(text="💬 Связаться со мной", callback_data="contact")
    )
    return builder.as_markup()


# ===== КАТАЛОГ =====
def get_catalog_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👶 Детские метрики и первый год", callback_data="cat_kids"))
    builder.row(InlineKeyboardButton(text="💒 Свадебные постеры и love story", callback_data="cat_wedding"))
    builder.row(InlineKeyboardButton(text="👨‍👩‍👧 Семейные постеры и travel-коллажи", callback_data="cat_family"))
    builder.row(InlineKeyboardButton(text="🎉 Праздничные постеры на день рождения и другие события", callback_data="cat_holiday"))
    builder.row(InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu"))
    return builder.as_markup()


# ===== КАТЕГОРИИ =====
def get_kids_category():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Все дизайны", callback_data="design_all"))
    builder.row(InlineKeyboardButton(text="Для девочки", callback_data="design_girl"))
    builder.row(InlineKeyboardButton(text="Для мальчика", callback_data="design_boy"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="catalog"))
    return builder.as_markup()


def get_product_card():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🖼️ Смотреть другие дизайны", callback_data="catalog"))
    builder.row(InlineKeyboardButton(text="✅ Заказать этот постер", callback_data="order"))
    return builder.as_markup()


# ===== ПОДАРКИ =====
def get_gift_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👶 На рождение малыша", callback_data="gift_baby"))
    builder.row(InlineKeyboardButton(text="🎂 На первый день рождения", callback_data="gift_birthday"))
    builder.row(InlineKeyboardButton(text="💒 Свадебный подарок", callback_data="gift_wedding"))
    builder.row(InlineKeyboardButton(text="👨‍👩‍👧 Для семьи и близких", callback_data="gift_family"))
    builder.row(InlineKeyboardButton(text="🎉 На любой праздник", callback_data="gift_any"))
    builder.row(InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu"))
    return builder.as_markup()


# ===== ЦЕНЫ =====
def get_prices_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💰 Цены на постеры", callback_data="prices_list"))
    builder.row(InlineKeyboardButton(text="📐 Форматы и материалы", callback_data="formats"))
    builder.row(InlineKeyboardButton(text="⏰ Сроки изготовления", callback_data="terms"))
    builder.row(InlineKeyboardButton(text="🚚 Доставка", callback_data="delivery"))
    builder.row(InlineKeyboardButton(text="💳 Способы оплаты", callback_data="payment"))
    builder.row(InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu"))
    return builder.as_markup()


# ===== ОБРАБОТЧИКИ =====
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! 👋\n\n"
        "Добро пожаловать в Lelayti!\n\n"
        "Мы создаём персонализированные постеры, которые сохранят ваши самые важные моменты.\n\n"
        "Выберите, что вас интересует:",
        reply_markup=get_main_menu()
    )


@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    data = callback.data

    if data == "main_menu":
        await callback.message.edit_caption(
            caption="Привет! 👋\n\nДобро пожаловать в Lelayti!\n\nМы создаём персонализированные постеры, которые сохранят ваши самые важные моменты.\n\nВыберите, что вас интересует:",
            reply_markup=get_main_menu()
        )

    elif data == "catalog":
        await callback.message.edit_text(
            text="📁 Каталог\n\nВыберите категорию, чтобы посмотреть примеры работ ✨",
            reply_markup=get_catalog_menu()
        )

    elif data == "cat_kids":
        await callback.message.edit_text(
            text="👶 Детские метрики\n\nЗдесь собраны примеры постеров с важными моментами первого года жизни. Выберите понравившийся дизайн, чтобы посмотреть подробнее:",
            reply_markup=get_kids_category()
        )

    elif data.startswith("design_"):
        await callback.message.edit_text(
            text="📸 Классическая метрика\nот 1 290 ₽\n\nНежный и лаконичный постер с основными данными о рождении. Можно добавить фото, иллюстрацию и выбрать цветовую гамму.\n\n• Любой текст и оформление\n• Форматы: A4, A3, A2\n• Цифровой файл или печать\n• Срок изготовления: 1–3 дня",
            reply_markup=get_product_card()
        )

    elif data == "order":
        await callback.message.edit_text(
            text="📝 Оформление заказа\n\nЗаполните, пожалуйста, информацию, чтобы я могла подготовить для вас постер 💛\n\n1/5\nКакой постер вы хотите заказать?",
            reply_markup=InlineKeyboardBuilder().as_markup()
        )

    elif data == "gift":
        await callback.message.edit_text(
            text="🎁 Подобрать подарок\n\nНе знаете, что выбрать? Я помогу найти идеальный вариант в зависимости от повода 💕",
            reply_markup=get_gift_menu()
        )

    elif data.startswith("gift_"):
        gift_texts = {
            "gift_baby": "👶 На рождение малыша — нежный подарок для молодых родителей",
            "gift_birthday": "🎂 На первый день рождения — памятный постер для именинника",
            "gift_wedding": "💒 Свадебный подарок — красивый постер для молодожёнов",
            "gift_family": "👨‍👩‍👧 Для семьи и близких — семейный портрет или коллаж",
            "gift_any": "🎉 На любой праздник — универсальный вариант"
        }
        await callback.message.edit_text(text=gift_texts.get(data, "Выберите подарок из меню"))

    elif data == "custom":
        await callback.message.edit_text(
            text="✏️ Индивидуальный заказ\n\nХотите что-то уникальное? Опишите вашу идею, и я создам постер специально для вас!"
        )

    elif data == "prices":
        await callback.message.edit_text(
            text="💰 Цены и доставка\n\nЗдесь вся важная информация о стоимости, форматах, сроках и способах получения.",
            reply_markup=get_prices_menu()
        )

    elif data == "prices_list":
        await callback.message.edit_text(text="💰 Цены на постеры\n\nКлассическая метрика — от 1 290 ₽\nАрт-метрика — от 1 290 ₽\nМетрика с фото — от 1 490 ₽")

    elif data == "formats":
        await callback.message.edit_text(text="📐 Форматы и материалы\n\nA4, A3, A2 — на выбор\nПлотная матовая или глянцевая бумага")

    elif data == "terms":
        await callback.message.edit_text(text="⏰ Сроки изготовления\n\n1–3 рабочих дня\nСрочные заказы — обсуждаются индивидуально")

    elif data == "delivery":
        await callback.message.edit_text(text="🚚 Доставка\n\nЭлектронная версия — сразу после оплаты\nПечать и отправка — 2–5 дней")

    elif data == "payment":
        await callback.message.edit_text(text="💳 Способы оплаты\n\nПеревод на карту, СБП, ЮMoney")

    elif data == "contact":
        await callback.message.answer(text="💬 Связаться со мной\n\nНапишите мне в личные сообщения!")

    await callback.answer()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен.")
