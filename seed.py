import random
import time
import requests
from datetime import datetime
#генерація подій для тестування системи
BACKEND_URL  = "http://localhost:8000"
NUM_EVENTS   = 30
DELAY_SEC    = 0.1

PLAYERS = [
    {"player_id": 1,  "player_name": "BlackWolf"},
    {"player_id": 2,  "player_name": "SkyRider"},
    {"player_id": 3,  "player_name": "DarkFox"},
    {"player_id": 4,  "player_name": "NightOwl"},
    {"player_id": 5,  "player_name": "IronWave"},
    {"player_id": 6,  "player_name": "StormKing"},
    {"player_id": 7,  "player_name": "RedPhoenix"},
    {"player_id": 8,  "player_name": "CoolBanana"},
]

def send_event(server_id, event_type, player_id, player_name):
    try:
        resp = requests.post(
            f"{BACKEND_URL}/events",
            json={
                "server_id":   server_id,
                "event_type":  event_type,
                "player_id":   player_id,
                "player_name": player_name,
            },
            timeout=5,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f" Помилка: {e}")
        return False


def main():
    print(f" Seed запущено — {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"   Backend: {BACKEND_URL}")
    print(f"   Подій:   {NUM_EVENTS}")
    print()

    try:
        requests.get(f"{BACKEND_URL}/", timeout=3)
    except Exception:
        print(" Backend недоступний.")
        return

    ok = 0
    fail = 0

    for i in range(NUM_EVENTS):
        player = random.choice(PLAYERS)
        event_type = "player_join" if random.random() < 0.65 else "player_leave"

        success = send_event(
            server_id="server1",
            event_type=event_type,
            player_id=player["player_id"],
            player_name=player["player_name"],
        )

        status = "✓" if success else "✗"
        label  = "JOIN " if event_type == "player_join" else "LEAVE"
        print(f"  {status} [{i+1:02d}/{NUM_EVENTS}] {label} — {player['player_name']}")

        if success:
            ok += 1
        else:
            fail += 1

        time.sleep(DELAY_SEC)

    print()
    print(f" Готово. Успішно: {ok}, Помилок: {fail}")


if __name__ == "__main__":
    main()
