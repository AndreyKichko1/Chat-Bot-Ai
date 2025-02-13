import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton
import requests
from dotenv import load_dotenv
from flask import Flask, request
from waitress import serve  # Импортируем Waitress

# Загружаем переменные из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен вашего бота
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Yandex GPT API ключ и endpoint
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# Ваш folder_id
FOLDER_ID = "b1g6k5v2qru86ki7fkto"

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Словарь для хранения истории сообщений
user_history = {}

# Функция для отправки запроса к Yandex GPT
def ask_yandex_gpt(prompt, user_id):
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }

    # Добавляем новое сообщение в историю
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append({"role": "user", "text": prompt})

    # Формируем данные для запроса
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 1000  # Увеличиваем количество токенов
        },
        "messages": user_history[user_id]
    }

    # Отправляем запрос
    response = requests.post(YANDEX_GPT_URL, json=data, headers=headers)
    if response.status_code == 200:
        # Добавляем ответ бота в историю
        bot_response = response.json().get("result", {}).get("alternatives", [])[0].get("message", {}).get("text", "").strip()
        user_history[user_id].append({"role": "assistant", "text": bot_response})
        return bot_response
    else:
        return f"Ошибка при запросе к Yandex GPT: {response.status_code}"

# Создаем меню
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("?? Сбросить всё"))
menu.add(KeyboardButton("?? Очистить историю"))
menu.add(KeyboardButton("?? Примеры запросов"))
menu.add(KeyboardButton("?? О боте"))
menu.add(KeyboardButton("?? Помощь"))

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user_history[user_id] = []  # Очищаем историю при старте
    await message.reply(
        "?? Привет! Я — *KichBot*, ваш персональный помощник с искусственным интеллектом. "
        "Напиши мне что-нибудь, и я постараюсь помочь!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=menu
    )

# Обработчик команды /help
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await show_help(message)

# Обработчик команды /clear
@dp.message_handler(commands=['clear'])
async def clear_command(message: types.Message):
    await clear_history(message)

# Обработчик текстовых сообщений
@dp.message_handler()
async def echo(message: types.Message):
    user_id = message.from_user.id
    user_message = message.text

    # Обработка команд из меню
    if user_message == "?? Сбросить всё":
        await send_welcome(message)
        return
    elif user_message == "?? Очистить историю":
        await clear_history(message)
        return
    elif user_message == "?? Примеры запросов":
        await show_examples(message)
        return
    elif user_message == "?? О боте":
        await about_bot(message)
        return
    elif user_message == "?? Помощь":
        await show_help(message)
        return

    # Показываем статус "печатает"
    await bot.send_chat_action(message.chat.id, "typing")
    await asyncio.sleep(1)  # Имитируем задержку

    # Обращаемся к Yandex GPT
    response = ask_yandex_gpt(user_message, user_id)
    await message.answer(response, parse_mode=ParseMode.MARKDOWN)

# Обработчик команды "Очистить историю"
async def clear_history(message: types.Message):
    user_id = message.from_user.id
    user_history[user_id] = []  # Очищаем историю
    await message.reply("?? *История очищена!* Бот больше не помнит предыдущие сообщения.", parse_mode=ParseMode.MARKDOWN)

# Обработчик команды "Примеры запросов"
async def show_examples(message: types.Message):
    # Генерируем примеры запросов с помощью Yandex GPT
    prompt = "Придумай 5 примеров запросов, которые можно задать умному боту."
    examples = ask_yandex_gpt(prompt, message.from_user.id)
    await message.reply(f"?? *Примеры запросов:*\n\n{examples}", parse_mode=ParseMode.MARKDOWN)

# Обработчик команды "О боте"
async def about_bot(message: types.Message):
    about_text = (
        "?? *О KichBot:*\n\n"
        "Я — ваш персональный помощник с искусственным интеллектом. Вот что я могу:\n"
        "- Отвечать на ваши вопросы.\n"
        "- Помнить контекст разговора.\n"
        "- Генерировать уникальные примеры запросов.\n"
        "- Очищать историю разговора.\n\n"
        "Используйте кнопки ниже, чтобы узнать больше!"
    )
    await message.reply(about_text, parse_mode=ParseMode.MARKDOWN)

# Обработчик команды "Помощь"
async def show_help(message: types.Message):
    help_text = (
        "?? *Помощь:*\n\n"
        "Если у вас возникли проблемы или вопросы, вот как вы можете связаться с моим создателем:\n"
        "?? *Email:* andrejkicko08@gmail.com\n"
        "?? *Telegram:* @Andrey09876542\n\n"
        "Просто напишите мне что-нибудь, и я постараюсь помочь!"
    )
    await message.reply(help_text, parse_mode=ParseMode.MARKDOWN)

# Инициализация Flask
app = Flask(__name__)

# Обработчик вебхука
@app.route('/webhook', methods=['POST'])
async def webhook():
    update = types.Update(**request.json)
    await dp.process_update(update)
    return 'ok'

# Запуск Waitress
if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=3000)  # Используем Waitress для запуска