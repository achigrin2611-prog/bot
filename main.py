import os
import logging
import urllib.parse
from dotenv import load_dotenv
from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- НАСТРОЙКИ ОПЛАТЫ (СБЕР) ---
PHONE_NUMBER = "+79066905758"
DEPOSIT_AMOUNT = 645
ANASTASIYA_ID = 5745114091


# --- МАШИНА СОСТОЯНИЙ (FSM) ---
class OrderState(StatesGroup):
    waiting_for_photo = State()
    waiting_for_details = State()
    choosing_payment = State()
    waiting_for_receipt = State()
    waiting_for_custom_text = State()


# --- КЛАВИАТУРЫ ---
def get_reply_keyboard():
    builder = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Главное меню")]],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие или напишите нам..."
    )
    return builder


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
    builder.row(InlineKeyboardButton(text="Все дизайны", callback_data="design_all"))
    builder.row(InlineKeyboardButton(text="Для девочки", callback_data="design_girl"))
    builder.row(InlineKeyboardButton(text="Для мальчика", callback_data="design_boy"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=back_to))
    return builder.as_markup()


def get_product_card():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Заказать этот постер", callback_data="order"))
    builder.row(InlineKeyboardButton(text="🔙 Назад к каталогу", callback_data="catalog"))
    return builder.as_markup()


def get_order_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📸 Классическая метрика (София)", callback_data="order_classic"))
    builder.row(InlineKeyboardButton(text="🎨 Другой дизайн из каталога", callback_data="order_catalog"))
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
    builder.row(InlineKeyboardButton(text="📐 Размеры", callback_data="formats"))
    builder.row(InlineKeyboardButton(text="⏰ Сроки изготовления", callback_data="terms"))
    builder.row(InlineKeyboardButton(text="🚚 Доставка", callback_data="delivery"))
    builder.row(InlineKeyboardButton(text="💳 Способы оплаты", callback_data="payment"))
    builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu"))
    return builder.as_markup()


# --- ОБРАБОТЧИКИ КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    args = message.text.split(maxsplit=1)

    if len(args) > 1:
        username = message.from_user.username or "скрыт"
        clean_text = urllib.parse.unquote(args[1])

        await message.answer("✅ Спасибо! Ваша заявка с сайта получена. Анастасия свяжется с вами в ближайшее время.")

        try:
            await bot.send_message(
                ANASTASIYA_ID,
                f"📩 **Новая заявка (с сайта)!**\n\n"
                f"От: @{username} (ID: {message.from_user.id})\n\n"
                f"{clean_text}"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке заявки с сайта: {e}")

        await message.answer("Чтобы вернуться в меню, используйте кнопку ниже 👇", reply_markup=get_reply_keyboard())
        return

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✨ Начать", callback_data="main_menu"))

    await message.answer(
        "Привет! 👋\n\n"
        "Добро пожаловать в Lelayti!\n\n"
        "Мы создаём персонализированные постеры, которые сохранят ваши самые важные моменты.\n\n"
        "Нажмите кнопку ниже, чтобы начать:",
        reply_markup=builder.as_markup()
    )
    await message.answer(
        "Используйте кнопку ниже, чтобы в любой момент вернуться в меню 👇",
        reply_markup=get_reply_keyboard()
    )


@dp.message(lambda message: message.text == "🏠 Главное меню")
async def back_to_main_from_reply(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Вы вернулись в главное меню. Выберите действие:",
        reply_markup=get_main_menu()
    )


# --- ЕДИНЫЙ ОБРАБОТЧИК ИНЛАЙН-КНОПОК ---
@dp.callback_query()
async def callback_handler(callback: CallbackQuery, state: FSMContext):
    data = callback.data

    if data == "pay_sber":
        await callback.message.edit_text(
            f"💳 **Оплата через СБП (Сбер)**\n\n"
            f"Сумма к оплате: **{DEPOSIT_AMOUNT} ₽**\n\n"
            f"📱 Номер для перевода: `{PHONE_NUMBER}`\n"
            f"(Сбербанк)\n\n"
            f"**Как перевести:**\n"
            f"1. Откройте приложение вашего банка.\n"
            f"2. Выберите «Перевод по номеру телефона» или «СБП».\n"
            f"3. Введите номер: `{PHONE_NUMBER}`\n"
            f"4. Укажите сумму: **{DEPOSIT_AMOUNT} ₽** и подтвердите.\n\n"
            f"После перевода **отправьте скриншот чека сюда** в чат.",
            parse_mode="Markdown"
        )
        await state.set_state(OrderState.waiting_for_receipt)
        await callback.answer()
        return

    if data == "main_menu":
        await state.clear()
        await callback.message.edit_text(
            text="Привет! 👋\n\nВыберите, что вас интересует:",
            reply_markup=get_main_menu()
        )
    elif data == "catalog":
        await callback.message.edit_text(text="📁 Каталог\n\nВыберите категорию:", reply_markup=get_catalog_menu())

    elif data in ["cat_kids", "cat_wedding", "cat_family"]:
        texts = {
            "cat_kids": "👶 Детские метрики\n\nВыберите дизайн:",
            "cat_wedding": "💒 Свадебные постеры\n\nВыберите дизайн:",
            "cat_family": "👨‍👩‍👧 Семейные постеры\n\nВыберите дизайн:"
        }
        await callback.message.edit_text(text=texts[data], reply_markup=get_kids_category(back_to="catalog"))

    elif data.startswith("design_"):
        await callback.message.edit_text(text="📸 Классическая метрика\nот 1 290 ₽\n\nВыберите действие:",
                                         reply_markup=get_product_card())

    elif data == "order":
        await callback.message.edit_text(
            text="📝 Оформление заказа\n\n1/5\nКакой постер вы хотите заказать?",
            reply_markup=get_order_menu()
        )
    elif data.startswith("order_"):
        await state.set_state(OrderState.waiting_for_photo)

        cancel_builder = InlineKeyboardBuilder()
        cancel_builder.row(InlineKeyboardButton(text="🔙 Отменить заказ", callback_data="main_menu"))

        await callback.message.edit_text(
            text="📝 Оформление заказа\n\n2/5\nПрикрепите фото:",
            reply_markup=cancel_builder.as_markup()
        )

    elif data == "gift":
        await callback.message.edit_text(text="🎁 Подобрать подарок\n\nВыберите повод:", reply_markup=get_gift_menu())

    elif data in ["gift_baby", "gift_birthday", "gift_wedding", "gift_family"]:
        if data in ["gift_baby", "gift_birthday"]:
            text = "👶 Детские метрики\n\nВыберите дизайн:"
        elif data == "gift_wedding":
            text = "💒 Свадебные постеры\n\nВыберите дизайн:"
        else:
            text = "👨‍👩‍👧 Семейные постеры\n\nВыберите дизайн:"

        await callback.message.edit_text(text=text, reply_markup=get_kids_category(back_to="gift"))

    elif data == "custom":
        await state.set_state(OrderState.waiting_for_custom_text)
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Отменить и в меню", callback_data="main_menu"))
        await callback.message.edit_text(
            text="✏️ Индивидуальный заказ\n\nОпишите вашу идею. Я передам это Анастасии, и она свяжется с вами!",
            reply_markup=builder.as_markup()
        )

    elif data == "prices":
        await callback.message.edit_text(text="💰 Цены и доставка\n\nИнформация:", reply_markup=get_prices_menu())
    elif data in ["prices_list", "formats", "terms", "delivery", "payment"]:
        info_texts = {
            "prices_list": "💰 Цены:\nКлассическая — от 1290 ₽\nАрт — от 1290 ₽\nС фото — от 1490 ₽",
            "formats": "📐 Доступные размеры:\nA4 (210×297 мм)\nA3 (297×420 мм)",
            "terms": "⏰ Сроки: 1–3 дня",
            "delivery": "🚚 Доставка: электронно или печать 2–5 дней",
            "payment": "💳 Оплата: СБП по номеру (Сбер)"
        }
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Назад к ценам", callback_data="prices"))
        await callback.message.edit_text(text=info_texts[data], reply_markup=builder.as_markup())

    elif data == "contact":
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu"))
        await callback.message.edit_text(text="💬 Связаться: @a_kishm", reply_markup=builder.as_markup())

    await callback.answer()


# --- ОБРАБОТЧИК ТЕКСТА И ФОТО (FSM) ---
@dp.message()
async def text_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state == OrderState.waiting_for_photo.state:
        if message.photo:
            await state.update_data(user_photo=message.photo[-1].file_id)

            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="🔙 Отменить заказ", callback_data="main_menu"))

            await message.answer("📸 Фото сохранено.\n\n3/5\nНапишите пожелания (текст, цвета):",
                                 reply_markup=builder.as_markup())
            await state.set_state(OrderState.waiting_for_details)
        else:
            await message.answer("Пожалуйста, отправьте фото.")

    elif current_state == OrderState.waiting_for_details.state:
        await state.update_data(order_text=message.text, username=message.from_user.username or "скрыт")

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="💳 Оплатить через СБП (Сбер)", callback_data="pay_sber"))
        builder.row(InlineKeyboardButton(text="🔙 Отменить заказ", callback_data="main_menu"))

        await message.answer(
            f"✅ Детали приняты!\nОсталась предоплата {DEPOSIT_AMOUNT} ₽.\nНажмите кнопку ниже:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(OrderState.choosing_payment)

    elif current_state == OrderState.choosing_payment.state:
        await message.answer("Нажмите на кнопку выше 👆")

    elif current_state == OrderState.waiting_for_receipt.state:
        if message.photo:
            user_data = await state.get_data()
            await message.answer(
                "✅ Скриншот получен! Передала Анастасии. Как только оплата подтвердится, я напишу вам!")
            try:
                await bot.send_message(ANASTASIYA_ID,
                                       f"🔥 **Заказ (Сбер)**\nОт: @{user_data.get('username')}\nПожелания: {user_data.get('order_text')}")
                if user_data.get('user_photo'):
                    await bot.send_photo(ANASTASIYA_ID, photo=user_data.get('user_photo'), caption="Фото к заказу")
                await bot.send_photo(ANASTASIYA_ID, photo=message.photo[-1].file_id, caption="🧾 Скриншот оплаты")
            except Exception as e:
                logger.error(f"Ошибка: {e}")
            await state.clear()

            await message.answer("Чтобы вернуться в меню, используйте кнопку ниже 👇", reply_markup=get_reply_keyboard())
        else:
            await message.answer("Отправьте скриншот чека.")

    elif current_state == OrderState.waiting_for_custom_text.state:
        username = message.from_user.username or "скрыт"
        await message.answer("✅ Спасибо! Я передала вашу идею Анастасии. Она свяжется с вами в ближайшее время.")

        try:
            await bot.send_message(
                ANASTASIYA_ID,
                f"✏️ **Новый индивидуальный заказ!**\n\n"
                f"От: @{username} (ID: {message.from_user.id})\n\n"
                f"Идея клиента:\n{message.text}"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке индивидуального заказа: {e}")

        await state.clear()
        await message.answer("Чтобы вернуться в меню, используйте кнопку ниже 👇", reply_markup=get_reply_keyboard())

    else:
        username = message.from_user.username or "скрыт"
        clean_text = urllib.parse.unquote(message.text).replace('*', '')

        await message.answer("✅ Спасибо! Ваша заявка принята. Анастасия свяжется с вами в ближайшее время.")

        try:
            await bot.send_message(
                ANASTASIYA_ID,
                f"📩 **Новая заявка (из бота)!**\n\n"
                f"От: @{username} (ID: {message.from_user.id})\n\n"
                f"Текст сообщения:\n{clean_text}"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке заявки: {e}")

        await message.answer("Чтобы вернуться в меню, используйте кнопку ниже 👇", reply_markup=get_reply_keyboard())


# --- НАСТРОЙКИ ДЛЯ RENDER (ВЕБХУКИ) ---
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "my-secret-token"


async def on_startup(bot: Bot):
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url, secret_token=WEBHOOK_SECRET)
        logger.info(f"Webhook установлен на {webhook_url}")
    else:
        logger.warning("RENDER_EXTERNAL_URL не задан! Вебхук не установлен.")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logger.info("Webhook удален")


def main():
    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    async def healthcheck(request):
        return web.Response(text="OK")

    app.router.add_get("/", healthcheck)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))


if __name__ == "__main__":
    main()