import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel
from psycopg2.extras import Json

from app.db import get_connection, release_connection
from app.ai_service import generate_ai_summary, generate_ai_chat

logger = logging.getLogger(__name__)
router = APIRouter()

TZ = "Europe/Kyiv"


@contextmanager
def db_cursor():
    conn = get_connection()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_connection(conn)


def _fetch_today_stats() -> tuple:
    with db_cursor() as cur:
        cur.execute(f"""
            SELECT
                COUNT(*),
                COUNT(*) FILTER (WHERE event_type = 'player_join'),
                COUNT(*) FILTER (WHERE event_type = 'player_leave'),
                COUNT(DISTINCT player_id)
            FROM events
            WHERE (created_at AT TIME ZONE '{TZ}')::date = CURRENT_DATE;
        """)
        total, joins, leaves, users = cur.fetchone()

        cur.execute(f"""
            SELECT EXTRACT(HOUR FROM created_at AT TIME ZONE '{TZ}'), COUNT(*)
            FROM events
            WHERE (created_at AT TIME ZONE '{TZ}')::date = CURRENT_DATE
            GROUP BY 1
            ORDER BY 2 DESC;
        """)
        hourly_data = cur.fetchall()

    return total, joins, leaves, users, hourly_data


def analyze_data(total, joins, leaves, users, hourly_data) -> tuple:
    if total == 0:
        status = "Сервер неактивний"
    elif joins > leaves:
        status = "Сервер активний"
    elif joins < leaves:
        status = "Спостерігається відтік гравців"
    else:
        status = "Стабільна активність"

    if joins > leaves:
        trend = "Зростання активності"
    elif joins < leaves:
        trend = "Зниження активності"
    else:
        trend = "Стабільна активність"

    peak_hour = None
    if hourly_data:
        peak_hour = int(max(hourly_data, key=lambda x: x[1])[0])

    insight = status if status == trend else f"{status}. {trend.lower()}."
    return status, trend, peak_hour, insight


def _upsert_player(cur, player_id: int, player_name: str, event_type: str):
    if event_type == "player_join":
        cur.execute("""
            INSERT INTO players (player_id, player_name, first_seen, last_seen, total_sessions)
            VALUES (%s, %s, NOW(), NOW(), 1)
            ON CONFLICT (player_id) DO UPDATE SET
                player_name    = EXCLUDED.player_name,
                last_seen      = NOW(),
                total_sessions = players.total_sessions + 1;
        """, (player_id, player_name))
    else:
        cur.execute("""
            INSERT INTO players (player_id, player_name, first_seen, last_seen, total_sessions)
            VALUES (%s, %s, NOW(), NOW(), 0)
            ON CONFLICT (player_id) DO UPDATE SET
                player_name = EXCLUDED.player_name,
                last_seen   = NOW();
        """, (player_id, player_name))


class EventIn(BaseModel):
    server_id: str
    event_type: str
    player_id: Optional[int] = None
    player_name: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class ChatIn(BaseModel):
    message: str


@router.get("/")
def root():
    return {"status": "ok"}


@router.post("/events")
def create_event(event: EventIn):
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO events (server_id, event_type, player_id, player_name, payload)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (event.server_id, event.event_type, event.player_id,
             event.player_name, Json(event.payload)),
        )
        event_id = cur.fetchone()[0]

        if event.player_id and event.event_type in ("player_join", "player_leave"):
            _upsert_player(cur, event.player_id, event.player_name, event.event_type)

    return {"status": "saved", "event_id": event_id}


@router.get("/report/today")
def report_today():
    total, joins, leaves, users, hourly_data = _fetch_today_stats()
    status, trend, peak_hour, insight = analyze_data(
        total, joins, leaves, users, hourly_data
    )
    return {
        "total_events": total,
        "joins": joins,
        "leaves": leaves,
        "unique_players": users,
        "status": status,
        "trend": trend,
        "peak_hour": peak_hour,
        "insight": insight,
    }


@router.get("/summary/today")
def summary_today():
    total, joins, leaves, users, hourly_data = _fetch_today_stats()
    status, trend, peak_hour, insight = analyze_data(
        total, joins, leaves, users, hourly_data
    )
    prompt = (
        f"Дані за сьогодні:\n"
        f"Події: {total}, Join: {joins}, Leave: {leaves}, "
        f"Унікальні гравці: {users}\n"
        f"Статус: {status}, Тренд: {trend}, Пік: {peak_hour}\n"
        f"Висновок: {insight}\n\n"
        "Зроби короткий аналітичний висновок без markdown."
    )
    return {"summary": generate_ai_summary(prompt)}


@router.post("/chat")
def chat(body: ChatIn):
    return {"reply": generate_ai_chat(body.message)}


@router.get("/stats/hourly")
def hourly_stats():
    with db_cursor() as cur:
        cur.execute(f"""
            SELECT EXTRACT(HOUR FROM created_at AT TIME ZONE '{TZ}') AS hour, COUNT(*)
            FROM events
            WHERE (created_at AT TIME ZONE '{TZ}')::date = CURRENT_DATE
            GROUP BY hour
            ORDER BY hour;
        """)
        rows = cur.fetchall()

    hourly = {int(r[0]): r[1] for r in rows}
    return {"hours": list(range(24)), "values": [hourly.get(h, 0) for h in range(24)]}


@router.get("/events/recent")
def get_recent_events():
    with db_cursor() as cur:
        cur.execute("""
            SELECT id, server_id, event_type, player_id, player_name, created_at
            FROM events
            ORDER BY created_at DESC
            LIMIT 20;
        """)
        rows = cur.fetchall()

    return {"events": [
        {
            "id": r[0], "server_id": r[1], "event_type": r[2],
            "player_id": r[3], "player_name": r[4], "created_at": str(r[5]),
        }
        for r in rows
    ]}


@router.get("/players/top")
def get_top_players():
    with db_cursor() as cur:
        cur.execute("""
            SELECT player_id, player_name, total_sessions, first_seen, last_seen
            FROM players
            ORDER BY total_sessions DESC
            LIMIT 10;
        """)
        rows = cur.fetchall()

    return {"players": [
        {
            "player_id": r[0],
            "player_name": r[1],
            "total_sessions": r[2],
            "first_seen": str(r[3]),
            "last_seen": str(r[4]),
        }
        for r in rows
    ]}
