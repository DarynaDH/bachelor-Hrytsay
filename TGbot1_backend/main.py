from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import Json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# =======================
# OpenRouter configuration
# =======================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# модель можна міняти для порівняння
AI_MODEL = "openai/gpt-4o-mini"
# приклади для тестів:
# "google/gemini-pro"
# "mistralai/mistral-7b"

# =======================
# FastAPI app
# =======================

app = FastAPI(title="TG Analytics Backend")

# =======================
# Database configuration
# =======================

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


# =======================
# Models
# =======================

class EventIn(BaseModel):
    server_id: str
    event_type: str
    player_id: Optional[int] = None
    player_name: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


# =======================
# AI helper function
# =======================

def generate_ai_summary(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "TG Analytics Bot"
    }

    payload = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Ти аналітичний асистент для ігрового сервера GTA. "
                           "Формуй стислий аналітичний висновок українською мовою "
                           "у нейтральному, діловому стилі. "
                           "Не використовуй емодзі."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception:
        return (
        "Аналітичний висновок наразі недоступний через тимчасову "
        "недоступність сервісу штучного інтелекту. "
        "Зібрані статистичні дані доступні, проте їх інтерпретація "
        "буде виконана після відновлення роботи AI-модуля."
    )



# =======================
# Routes
# =======================

@app.get("/")
def root():
    return {"status": "ok", "message": "Backend is running"}


@app.post("/events")
def create_event(event: EventIn):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO events (server_id, event_type, player_id, player_name, payload)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (
            event.server_id,
            event.event_type,
            event.player_id,
            event.player_name,
            Json(event.payload),
        ),
    )

    event_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return {"status": "saved", "event_id": event_id}


@app.get("/report/today")
def report_today():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM events
        WHERE created_at::date = CURRENT_DATE;
    """)
    total_events = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM events
        WHERE created_at::date = CURRENT_DATE
          AND event_type = 'player_join';
    """)
    joins = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM events
        WHERE created_at::date = CURRENT_DATE
          AND event_type = 'player_leave';
    """)
    leaves = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(DISTINCT player_id)
        FROM events
        WHERE created_at::date = CURRENT_DATE
          AND player_id IS NOT NULL;
    """)
    unique_players = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "date": "today",
        "total_events": total_events,
        "joins": joins,
        "leaves": leaves,
        "unique_players": unique_players
    }


@app.get("/summary/today")
def summary_today():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total_events,
            COUNT(*) FILTER (WHERE event_type = 'player_join') AS joins,
            COUNT(*) FILTER (WHERE event_type = 'player_leave') AS leaves,
            COUNT(DISTINCT player_id) AS unique_players
        FROM events
        WHERE created_at::date = CURRENT_DATE;
    """)
    total_events, joins, leaves, unique_players = cur.fetchone()

    cur.close()
    conn.close()

    prompt = f"""
Статистика ігрового сервера GTA за сьогодні:

- Загальна кількість подій: {total_events}
- Підключень гравців (join): {joins}
- Виходів гравців (leave): {leaves}
- Унікальних гравців: {unique_players}

Сформуй короткий аналітичний висновок (3–4 речення):
- опиши поточну активність сервера;
- оціни рівень активності (високий / середній / низький);
- надай можливе пояснення або інтерпретацію ситуації.
"""


    summary_text = generate_ai_summary(prompt)

    return {
        "date": "today",
        "summary": summary_text
    }
