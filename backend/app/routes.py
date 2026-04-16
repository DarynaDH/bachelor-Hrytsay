from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from psycopg2.extras import Json

from app.db import get_connection
from app.ai_service import generate_ai_summary, generate_ai_chat

router = APIRouter()


class EventIn(BaseModel):
    server_id: str
    event_type: str
    player_id: Optional[int] = None
    player_name: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


@router.get("/")
def root():
    return {"status": "ok"}


@router.post("/events")
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


@router.get("/report/today")
def report_today():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*),
               COUNT(*) FILTER (WHERE event_type = 'player_join'),
               COUNT(*) FILTER (WHERE event_type = 'player_leave'),
               COUNT(DISTINCT player_id)
        FROM events
        WHERE created_at::date = CURRENT_DATE;
    """)

    total, joins, leaves, users = cur.fetchone()

    cur.close()
    conn.close()

    return {
        "total_events": total,
        "joins": joins,
        "leaves": leaves,
        "unique_players": users
    }


@router.get("/summary/today")
def summary_today():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*),
               COUNT(*) FILTER (WHERE event_type = 'player_join'),
               COUNT(*) FILTER (WHERE event_type = 'player_leave'),
               COUNT(DISTINCT player_id)
        FROM events
        WHERE created_at::date = CURRENT_DATE;
    """)

    total, joins, leaves, users = cur.fetchone()

    cur.close()
    conn.close()

    prompt = f"""
    Події: {total}
    Join: {joins}
    Leave: {leaves}
    Унікальні: {users}
    """

    return {"summary": generate_ai_summary(prompt)}


@router.post("/chat")
def chat(message: Dict[str, str]):
    return {"reply": generate_ai_chat(message.get("message", ""))}