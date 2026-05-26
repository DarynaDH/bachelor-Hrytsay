import logging
import os

import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"


MODEL_PRIMARY  = "openai/gpt-5.4"
MODEL_FALLBACK = "qwen/qwen3.5-397b-a17b"


def _call_api(model: str, system: str, user: str, timeout: int = 60) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _call_with_fallback(system: str, user: str, timeout: int = 60) -> str:
    try:
        return _call_api(MODEL_PRIMARY, system, user, timeout=timeout)
    except requests.exceptions.Timeout:
        logger.warning("Primary model %s timeout, switching to fallback %s",
                       MODEL_PRIMARY, MODEL_FALLBACK)
    except Exception as e:
        logger.warning("Primary model %s failed: %s, switching to fallback %s",
                       MODEL_PRIMARY, e, MODEL_FALLBACK)

    try:
        result = _call_api(MODEL_FALLBACK, system, user, timeout=timeout)
        logger.info("Fallback model %s responded successfully", MODEL_FALLBACK)
        return result
    except requests.exceptions.Timeout:
        logger.error("Fallback model %s also timeout", MODEL_FALLBACK)
        return "❌ Перевищено час очікування відповіді AI."
    except Exception as e:
        logger.error("Fallback model %s also failed: %s", MODEL_FALLBACK, e)
        return "❌ AI-сервіс тимчасово недоступний"


def generate_ai_summary(prompt: str) -> str:
    system = (
        "Ти аналітик GTA сервера. "
        "Формуй короткі та зрозумілі аналітичні висновки для Telegram. "
        "Відповідай українською мовою. Не більше 5-6 речень."
    )
    return _call_with_fallback(system, prompt, timeout=60)


def generate_ai_chat(user_message: str) -> str:
    system = (
        "Ти помічник GTA сервера. "
        "Відповідай коротко, зрозуміло та українською мовою. "
        "Не більше 5-6 речень. "
        "Якщо запит незрозумілий (наприклад: '123', '.', '!!!'), "
        "попроси користувача уточнити питання."
    )
    return _call_with_fallback(system, user_message, timeout=30)