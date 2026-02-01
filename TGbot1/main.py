import asyncio
import logging
import requests

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import os
from dotenv import load_dotenv

load_dotenv()

# =======================
# CONFIG
# =======================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# адреса backend FastAPI
BACKEND_URL = os.getenv("BACKEND_URL")


# =======================
# LOGGING
# =======================

logging.basicConfig(level=logging.INFO)

# =======================
# BOT & DISPATCHER
# =======================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =======================
# COMMANDS
# =======================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привіт! 🤖\n\n"
        "Я бот для аналітики ігрового сервера.\n\n"
        "Доступні команди:\n"
        "/report — статистика за сьогодні\n"
        "/summary — AI-аналітика за сьогодні"
    )


@dp.message(Command("report"))
async def report(message: Message):
    try:
        response = requests.get(f"{BACKEND_URL}/report/today", timeout=5)
        response.raise_for_status()
        data = response.json()

        text = (
            "📊 Звіт за сьогодні:\n\n"
            f"• Подій всього: {data['total_events']}\n"
            f"• Join: {data['joins']}\n"
            f"• Leave: {data['leaves']}\n"
            f"• Унікальні гравці: {data['unique_players']}"
        )

        await message.answer(text)

    except Exception as e:
        await message.answer("❌ Помилка отримання звіту з сервера.")


@dp.message(Command("summary"))
async def summary(message: Message):
    try:
        response = requests.get(f"{BACKEND_URL}/summary/today", timeout=10)
        response.raise_for_status()
        data = response.json()

        summary_text = data.get("summary", "Аналітичний висновок недоступний.")

        await message.answer(
            "🧠 AI-аналітика за сьогодні:\n\n"
            f"{summary_text}"
        )

    except Exception:
        await message.answer("❌ Помилка отримання AI-аналітики.")


# =======================
# START BOT
# =======================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
