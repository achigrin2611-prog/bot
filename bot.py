import os
import logging
import asyncio
import urllib.parse
import glob
from dotenv import load_dotenv
from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ID КАРТИНОК ДЛЯ МЕТРИК ---
PHOTO_KIDS_1 = "AgACAgIAAxkBAAIBmGrp8AtEHNcbDVxw0nnCAAHU675X-gAClyBrG_8HUUs6jrIwrwbNNgEAAwIAA3kAAz0E"
PHOTO_KIDS_2 = "AgACAgIAAxkBAAIBn2rp8RxMLeogjIaFBdYS5kDhBTjYAAKcIGsb_wdRS2MiPEbD6mNsAQADAgADeQADPQQ"
PHOTO_KIDS_3 = "AgACAgIAAxkBAAIB72rp9kXATzZaKW2Z_2zQ75UPl1MwAAKsImsb-mtQSw3JjMm4OnifAQADAgADeQADPQQ"


# --- МАШИНА СОСТОЯНИЙ (FSM) ---
class OrderState(StatesGroup):
    waiting_for_photo = State()
    waiting_for_details = State()
    waiting_for_custom_text = State()


# --- КЛАВИАТУРЫ ---
def get_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие или напишите нам..."
    )


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


def get_catalog_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👶 Детские метрики", callback_data="cat_kids"))
    builder.row(InlineKeyboardButton(text="💒 Свадебные постеры", callback_data="cat_wedding"))
    builder.row(InlineKeyboardButton(text="👨‍👩‍👧 Семейные постеры", callback_data="cat_family"))
    builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu"))
    return builder.as_markup()


def get_kids_category(back_to="catalog"):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Все дизайны", callback_data="design_all_kids"))
    builder.row(InlineKeyboardButton(text="Для девочки", callback_data="design_girl"))
    builder.row(InlineKeyboardButton(text="Для мальчика", callback_data="design_boy"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=back_to))
    return builder.as_markup()


def get_general_category(back_to="catalog"):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Посмотреть примеры", callback_data="design_all_general"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=back_to))
    return builder.as_markup()


def get_product_card(category="kids"):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Заказать этот постер", callback_data=f"order_{category}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад к каталогу", callback_data="catalog"))
    return builder.as_markup()


def get_order_menu(category="kids"):
    builder = InlineKeyboardBuilder()
    if category == "kids":
        builder.row(InlineKeyboardButton(text="📸 Классическая метрика (Коллаж)", callback_data="order_classic"))
        builder.row(InlineKeyboardButton(text="🖼 Портрет с текстом", callback_data="order_portrait"))
    elif category == "wedding":
        builder.row(InlineKeyboardButton(text="💒 Свадебный коллаж", callback_data="order_wed_collage"))
        builder.row(InlineKeyboardButton(text="📅 Постер с датой", callback_data="order_wed_date"))
    elif category == "family":
        builder.row(InlineKeyboardButton(text="👨‍👩‍👧 Семейный коллаж", callback_data="order_fam_collage"))
        builder.row(InlineKeyboardButton(text="🖼 Портрет с текстом", callback_data="order_fam_portrait"))

    builder.row(InlineKeyboardButton(text="✏️ Свой вариант", callback_data="order_custom"))
    builder.row(InlineKeyboardButton(text="🔙 Отменить и в меню", callback_data="main_menu"))
    return builder.as_markup()


def get_gift_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👶 На рождение малыша", callback_data="gift_baby"))
    builder.row(InlineKeyboardButton(text="🎂 На первый день рождения", callback_data="gift_birthday"))
    builder.row(InlineKeyboardButton(text="💒 Свадебный подарок", callback_data="gift_wedding"))
    builder.row(InlineKeyboardButton(text="👨‍👩‍👧 Для семьи и близких", callback_data="gift_family"))
    builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu"))
    return builder.as_markup()


def get_prices_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💰 Цены на постеры", callback_data="prices_list"))
    builder.row(InlineKeyboardButton(text="⏰ Сроки изготовления", callback_data="terms"))
    builder.row(InlineKeyboardButton(text="🚚 Доставка", callback_data="delivery"))
    builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu"))
    return builder.as_markup()


# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        username = message.from_user.username or "скрыт"
        clean_text = urllib.parse.unquote(args[1])
        await message.answer("✅ Спасибо! Ваша заявка с сайта получена. Анастасия свяжется с вами в ближайшее время.")
        try:
            await bot.send_message(ADMIN_ID,
                                   f"📩 **Новая заявка (с сайта)!**\n\nОт: @{username} (ID: {message.from_user.id})\n\n{clean_text}")
        except Exception as e:
            logger.error(f"Ошибка при отправке заявки с сайта: {e}")
        await message.answer("Чтобы вернуться в меню, используйте кнопку ниже 👇", reply_markup=get_reply_keyboard())
        return

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✨ Начать", callback_data="main_menu"))
    await message.answer(
        "Привет! 👋\n\nДобро пожаловать в Lelayti!\n\nМы создаём персонализированные постеры, которые сохранят ваши самые важные моменты.\n\nНажмите кнопку ниже, чтобы начать:",
        reply_markup=builder.as_markup()
    )
    await message.answer("Используйте кнопку ниже, чтобы в любой момент вернуться в меню 👇",
                         reply_markup=get_reply_keyboard())


@dp.message(lambda message: message.text == "🏠 Главное меню")
async def back_to_main_from_reply(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Вы вернулись в главное меню. Выберите действие:", reply_markup=get_main_menu())


@dp.callback_query()
async def callback_handler(callback: CallbackQuery, state: FSMContext):
    data = callback.data

    if data == "main_menu":
        await state.clear()
        await callback.message.edit_text(text="Привет! 👋\n\nВыберите, что вас интересует:",
                                         reply_markup=get_main_menu())

    elif data == "catalog":
        await callback.message.edit_text(text="📁 Каталог\n\nВыберите категорию:", reply_markup=get_catalog_menu())

    elif data == "cat_kids":
        await callback.message.edit_text(text="👶 Детские метрики\n\nВыберите дизайн:",
                                         reply_markup=get_kids_category(back_to="catalog"))
    elif data == "cat_wedding":
        await callback.message.edit_text(text="💒 Свадебные постеры\n\nВыберите дизайн:",
                                         reply_markup=get_general_category(back_to="catalog"))
    elif data == "cat_family":
        await callback.message.edit_text(text="👨‍👩‍👧 Семейные постеры\n\nВыберите дизайн:",
                                         reply_markup=get_general_category(back_to="catalog"))

    elif data.startswith("design_"):
        if "kids" in data or "girl" in data or "boy" in data:
            await callback.message.answer_photo(PHOTO_KIDS_1, caption="📸 Пример: Коллаж")
            await callback.message.answer_photo(PHOTO_KIDS_2, caption="🖼 Пример: Портрет с текстом")
            await callback.message.answer_photo(PHOTO_KIDS_3, caption="📸 Пример: Коллаж на голубом фоне")
            await callback.message.answer(text="Вам нравится? Вы можете заказать постер:",
                                          reply_markup=get_product_card("kids"))

        elif data == "design_all_general":
            is_wedding = False
            if callback.message.text and "Свадебные" in callback.message.text:
                is_wedding = True

            # Жестко прописываем файлы, чтобы точно нашлись
            if is_wedding:
                files = ["wedding1.jpg", "wedding2.jpg", "wedding3.jpg", "wedding4.jpg", "wedding5.jpg"]
                for file_path in files:
                    try:
                        photo = FSInputFile(file_path)
                        await callback.message.answer_photo(photo, caption="Свадебный постер")
                    except Exception as e:
                        logger.error(f"Ошибка отправки {file_path}: {e}")
                await callback.message.answer(text="Вам нравится? Вы можете заказать постер:",
                                              reply_markup=get_product_card("wedding"))
            else:
                files = ["family1.jpg", "family2.jpg", "family3.jpg", "family4.jpg"]
                for file_path in files:
                    try:
                        photo = FSInputFile(file_path)
                        await callback.message.answer_photo(photo, caption="Семейный постер")
                    except Exception as e:
                        logger.error(f"Ошибка отправки {file_path}: {e}")
                await callback.message.answer(text="Вам нравится? Вы можете заказать постер:",
                                              reply_markup=get_product_card("family"))

    elif data.startswith("order_") and data in ["order_kids", "order_wedding", "order_family"]:
        category = data.split("_")[1]
        await callback.message.edit_text(
            text="📝 Оформление заказа\n\n1/4\nКакой постер вы хотите заказать?",
            reply_markup=get_order_menu(category)
        )

    elif data.startswith("order_classic") or data.startswith("order_portrait") or data.startswith(
            "order_wed") or data.startswith("order_fam"):
        await state.set_state(OrderState.waiting_for_photo)
        cancel_builder = InlineKeyboardBuilder()
        cancel_builder.row(InlineKeyboardButton(text="🔙 Отменить заказ", callback_data="main_menu"))
        await callback.message.edit_text(
            text="📝 Оформление заказа\n\n2/4\nПрикрепите фото (или несколько):",
            reply_markup=cancel_builder.as_markup()
        )

    elif data == "custom" or data == "order_custom":
        await state.set_state(OrderState.waiting_for_custom_text)
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Отменить и в меню", callback_data="main_menu"))
        await callback.message.edit_text(
            text="✏️ Индивидуальный заказ\n\nОпишите вашу идею (что бы вы хотели видеть на постере, какие цвета, пожелания). Я передам это Анастасии, и она свяжется с вами!",
            reply_markup=builder.as_markup()
        )

    elif data == "gift":
        await callback.message.edit_text(text="🎁 Подобрать подарок\n\nВыберите повод:", reply_markup=get_gift_menu())
    elif data in ["gift_baby", "gift_birthday"]:
        await callback.message.edit_text(text="👶 Детские метрики\n\nВыберите дизайн:",
                                         reply_markup=get_kids_category(back_to="gift"))
    elif data in ["gift_wedding", "gift_family"]:
        await callback.message.edit_text(text="🖼 Выберите дизайн:", reply_markup=get_general_category(back_to="gift"))

    elif data == "prices":
        await callback.message.edit_text(text="💰 Цены и доставка\n\nИнформация:", reply_markup=get_prices_menu())

    elif data == "prices_list":
        try:
            photo = FSInputFile("price.jpg")
            await callback.message.answer_photo(photo, caption="Актуальные цены:")
        except Exception as e:
            logger.error(f"Ошибка при отправке прайса: {e}")
            await callback.message.answer("Не удалось загрузить картинку с ценами. Пожалуйста, напишите нам.")

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Назад к ценам", callback_data="prices"))
        await callback.message.answer("Выберите действие:", reply_markup=builder.as_markup())

    elif data == "terms":
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Назад к ценам", callback_data="prices"))
        await callback.message.edit_text(
            text="⏰ **Сроки изготовления:**\n\n• Электронный формат: 1-2 дня\n• Печатный формат: 1-3 дня + доставка",
            reply_markup=builder.as_markup(), parse_mode="Markdown")

    elif data == "delivery":
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Назад к ценам", callback_data="prices"))
        await callback.message.edit_text(
            text="🚚 **Доставка**\n\nМы отправляем заказы удобным для вас способом — вы можете выбрать любого подходящего оператора доставки.\n\nСтоимость доставки оплачивается получателем отдельно и рассчитывается согласно тарифам выбранной службы доставки.\n\nСроки и условия доставки зависят от выбранного оператора и направления отправления.",
            reply_markup=builder.as_markup(), parse_mode="Markdown")

    elif data == "contact":
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu"))
        await callback.message.edit_text(text="💬 Связаться: @a_kishm", reply_markup=builder.as_markup())

    await callback.answer()


@dp.message()
async def text_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state == OrderState.waiting_for_photo.state:
        if message.photo:
            await state.update_data(user_photo=message.photo[-1].file_id)
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="🔙 Отменить заказ", callback_data="main_menu"))
            await message.answer("📸 Фото сохранено.\n\n3/4\nНапишите пожелания (текст, цвета, имена и т.д.):",
                                 reply_markup=builder.as_markup())
            await state.set_state(OrderState.waiting_for_details)
        else:
            await message.answer("Пожалуйста, отправьте фото.")

    elif current_state == OrderState.waiting_for_details.state:
        if message.text:
            await state.update_data(order_text=message.text, username=message.from_user.username or "скрыт")
            user_data = await state.get_data()
            await message.answer(
                "✅ Детали приняты!\n\nАнастасия свяжется с вами в ближайшее время для обсуждения деталей и оплаты.")

            try:
                await bot.send_message(ADMIN_ID,
                                       f"🔥 **Новый заказ!**\nОт: @{user_data.get('username')}\nПожелания: {user_data.get('order_text')}")
                if user_data.get('user_photo'):
                    await bot.send_photo(ADMIN_ID, photo=user_data.get('user_photo'), caption="Фото к заказу")
            except Exception as e:
                logger.error(f"Ошибка: {e}")

            await state.clear()
            await message.answer("Чтобы вернуться в меню, используйте кнопку ниже 👇", reply_markup=get_reply_keyboard())
        else:
            await message.answer("Пожалуйста, напишите пожелания текстом.")

    elif current_state == OrderState.waiting_for_custom_text.state:
        if message.text:
            username = message.from_user.username or "скрыт"
            await message.answer("✅ Спасибо! Я передала вашу идею Анастасии. Она свяжется с вами в ближайшее время.")
            try:
                await bot.send_message(ADMIN_ID,
                                       f"✏️ **Новый индивидуальный заказ!**\n\nОт: @{username} (ID: {message.from_user.id})\n\nИдея клиента:\n{message.text}")
            except Exception as e:
                logger.error(f"Ошибка при отправке индивидуального заказа: {e}")
            await state.clear()
            await message.answer("Чтобы вернуться в меню, используйте кнопку ниже 👇", reply_markup=get_reply_keyboard())
        else:
            await message.answer("Пожалуйста, опишите вашу идею текстом.")

    else:
        username = message.from_user.username or "скрыт"
        text_to_send = message.text or message.caption or "Без текста"
        clean_text = urllib.parse.unquote(text_to_send).replace('*', '')

        await message.answer("✅ Спасибо! Ваша заявка принята. Анастасия свяжется с вами в ближайшее время.")
        try:
            await bot.send_message(ADMIN_ID,
                                   f"📩 **Новая заявка (из бота)!**\n\nОт: @{username} (ID: {message.from_user.id})\n\nТекст сообщения:\n{clean_text}")
        except Exception as e:
            logger.error(f"Ошибка при отправке заявки: {e}")
        await message.answer("Чтобы вернуться в меню, используйте кнопку ниже 👇", reply_markup=get_reply_keyboard())


# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle_ping(request):
    return web.Response(text="Bot is running!")


async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Веб-сервер запущен на порту {port}")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await start_web_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен.")