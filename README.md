# Telegram Bot

Бот  на **aiogram 3.x**

## Установка

```bash
pip install -r requirements.txt
```

## Локальный запуск

1. Создай бота через [@BotFather](https://t.me/BotFather) → получи токен
2. Узнай свой ID через [@userinfobot](https://t.me/userinfobot)
3. Скопируй `.env.example` в `.env` и заполни:

```env
BOT_TOKEN=твой_токен_от_BotFather
ADMIN_ID=твой_telegram_id
```

4. Запуск:

```bash
python bot.py
```

## Деплой на Render (бесплатно, работает 24/7)

### Шаг 1: Подготовка

1. Создай аккаунт на [render.com](https://render.com)
2. Запуш код в **GitHub** репозиторий

### Шаг 2: Создай сервис на Render

1. Войди в [Render Dashboard](https://dashboard.render.com)
2. Нажми **"New +" → "Public Website"**
3. Подключи свой GitHub репозиторий
4. Настройки:
   - **Name:** любой (например `sister-bot`)
   - **Region:** выбери ближайший
   - **Branch:** main
   - **Root Directory:** оставь пустым
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`

### Шаг 3: Добавь переменные окружения

В разделе **"Environment"** добавь:

```
BOT_TOKEN=твой_токен
ADMIN_ID=твой_id
```

### Шаг 4: Deploy

Нажми **"Create Service"** и жди ~2 минуты. Бот запустится и будет работать 24/7!

## Команды бота

| Команда   | Описание           |
|-----------|--------------------|
| /start    | Начать работу      |
| /help     | Справка            |
| /stats    | Статистика         |

## Структура проекта

```
├── bot.py          # Основной файл бота
├── requirements.txt# Зависимости
├── .env.example    # Пример переменных окружения
└── README.md       # Эта документация
```
