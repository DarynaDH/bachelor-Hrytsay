import asyncio
import logging
import requests
import re

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import os
from dotenv import load_dotenv

# =======================
# ENV
# =======================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL")

ADMIN_IDS = [632551809]

# =======================
# LOGGING
# =======================

logging.basicConfig(level=logging.INFO)

# =======================
# BOT
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
        "Доступно:\n"
        "• Напиши будь-яке повідомлення — я відповім\n"
        "• /report — статистика\n"
        "• /summary — тільки для адміна"
    )


# ---------- REPORT ----------
@dp.message(Command("report"))
async def report(message: Message):
    try:
        response = requests.get(f"{BACKEND_URL}/report/today", timeout=5)
        response.raise_for_status()
        data = response.json()

        text = (
            "📊 Звіт за сьогодні:\n\n"
            f"• Подій всього: {data.get('total_events', 0)}\n"
            f"• Join: {data.get('joins', 0)}\n"
            f"• Leave: {data.get('leaves', 0)}\n"
            f"• Унікальні гравці: {data.get('unique_players', 0)}"
        )

        await message.answer(text)

    except Exception as e:
        print("REPORT ERROR:", e)
        await message.answer("❌ Помилка отримання звіту.")


# ---------- SUMMARY ----------
@dp.message(Command("summary"))
async def summary(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У тебе немає доступу до цієї команди.")
        return

    try:
        response = requests.get(f"{BACKEND_URL}/summary/today", timeout=30)
        response.raise_for_status()
        data = response.json()

        summary_text = data.get("summary", "Немає даних")

        # 🔥 чистимо markdown
        summary_text = re.sub(r'[#*`_>\-]', '', summary_text)
        summary_text = re.sub(r'\n\s*\n', '\n\n', summary_text)

        # 🔥 обмеження Telegram
        summary_text = summary_text[:4000]

        await message.answer(
            "🧠 AI-аналітика:\n\n" + summary_text
        )

    except Exception as e:
        print("SUMMARY ERROR:", e)
        await message.answer("❌ Помилка AI-аналітики.")


# ---------- CHAT ----------
@dp.message()
async def chat_handler(message: Message):
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"message": message.text},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        reply = data.get("reply", "Немає відповіді.")

        # чистка markdown
        reply = re.sub(r'[#*`_>\-]', '', reply)
        reply = reply[:4000]

        await message.answer(reply)

    except Exception as e:
        print("CHAT ERROR:", e)
        await message.answer("❌ Помилка з'єднання з сервером.")


# =======================
# START
# =======================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())