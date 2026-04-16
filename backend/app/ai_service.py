import requests
from dotenv import load_dotenv
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(BASE_DIR, ".env")

load_dotenv(env_path)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_ANALYSIS = "anthropic/claude-4.6-opus"
MODEL_CHAT = "x-ai/grok-4-fast"


def generate_ai_summary(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_ANALYSIS,
        "messages": [
            {"role": "system", "content": "Ти аналітик GTA сервера."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return "AI недоступний"


def generate_ai_chat(user_message: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_CHAT,
        "messages": [
            {"role": "system", "content": "Ти помічник GTA сервера"},
            {"role": "user", "content": user_message}
        ]
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return "Сервіс недоступний"