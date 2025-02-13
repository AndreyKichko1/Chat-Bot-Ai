import logging
import os
import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton
import requests
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токены
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
FOLDER_ID = "b1g6k5v2qru86ki7fkto"

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
user_history = {}

def ask_yandex_gpt(prompt, user_id):
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }

    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append({"role": "user", "text": prompt})

    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 1000
        },
        "messages": user_history[user_id]
    }

    response = requests.post(YANDEX_GPT_URL, json=data, headers=headers)
    if response.status_code == 200:
        bot_response = response.json().get("result", {}).get("alternatives", [])[0].get("message", {}).get("text", "").strip()
        user_history[user_id].append({"role": "assistant", "text": bot_response})
        return bot_response
    else:
        return f"Ошибка: {response.status_code}"

# Меню и обработчики (оставить без изменений, как в вашем коде)
# ... [Ваши обработчики сообщений без изменений] ...

# Обработчик для Vercel
async def vercel_handler(request):
    try:
        update = types.Update(**json.loads(request.body))
        await dp.process_update(update)
        return {"statusCode": 200, "body": "OK"}
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {"statusCode": 500, "body": str(e)}