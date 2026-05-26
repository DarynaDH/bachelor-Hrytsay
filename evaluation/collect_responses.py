import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv
#pбір відповідей моделей через OpenRouter

for env_path in [".env", "../.env", "../../.env", "../backend/.env"]:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break
else:
    load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

if not OPENROUTER_API_KEY:
    print(" OPENROUTER_API_KEY не знайдено в .env")
    sys.exit(1)

MODELS = {
    "claude":  "anthropic/claude-opus-4.6",
    "gemini":  "google/gemini-3.1-pro",
    "gpt":     "openai/gpt-5.4",
    "glm":     "z-ai/glm-5",
    "qwen":    "qwen/qwen3.5-397b-a17b",
    "grok":    "x-ai/grok-4.20",
    "kimi":    "moonshotai/kimi-k2.5",
}

TIME_OF_DAY = ["morning", "day", "evening", "night"]


def load_queries():
    path = Path(__file__).parent / "test_queries.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["queries"]


def call_model(model_slug, query_text, timeout=120):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_slug,
        "messages": [{"role": "user", "content": query_text}],
    }

    start = time.time()
    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=timeout
        )
        elapsed = time.time() - start
        response.raise_for_status()
        data = response.json()

        return {
            "ok":              True,
            "response_text":   data["choices"][0]["message"]["content"],
            "elapsed_seconds": round(elapsed, 2),
            "prompt_tokens":   data.get("usage", {}).get("prompt_tokens"),
            "completion_tokens": data.get("usage", {}).get("completion_tokens"),
            "total_tokens":    data.get("usage", {}).get("total_tokens"),
            "error":           None,
        }
    except requests.exceptions.Timeout:
        return {
            "ok": False, "response_text": None,
            "elapsed_seconds": round(time.time() - start, 2),
            "prompt_tokens": None, "completion_tokens": None, "total_tokens": None,
            "error": "TIMEOUT",
        }
    except Exception as e:
        return {
            "ok": False, "response_text": None,
            "elapsed_seconds": round(time.time() - start, 2),
            "prompt_tokens": None, "completion_tokens": None, "total_tokens": None,
            "error": str(e),
        }
def test_one_model(model_key, time_of_day, queries):
    model_slug = MODELS[model_key]
    results = []

    print(f"\n{'='*60}")
    print(f" МОДЕЛЬ: {model_key} ({model_slug})")
    print(f" ЧАС ДОБИ: {time_of_day}")
    print(f" ЗАПИТІВ: {len(queries)}")
    print('='*60)

    for i, q in enumerate(queries, 1):
        print(f"  [{i:2d}/{len(queries)}] {q['id']} ({q['category']})... ", end="", flush=True)
        result = call_model(model_slug, q["text"])

        if result["ok"]:
            print(f" {result['elapsed_seconds']:.1f}с | {result['total_tokens']} токенів")
        else:
            print(f" ПОМИЛКА: {result['error']}")

        results.append({
            "query_id":      q["id"],
            "category":      q["category"],
            "query_text":    q["text"],
            **result,
        })

    return {
        "model_key":     model_key,
        "model_slug":    model_slug,
        "time_of_day":   time_of_day,
        "timestamp":     datetime.now().isoformat(),
        "total_queries": len(queries),
        "successful":    sum(1 for r in results if r["ok"]),
        "results":       results,
    }
def save_results(data, time_of_day, model_key):
    out_dir = Path(__file__).parent / "responses"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"responses_{time_of_day}_{model_key}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Збережено: {out_path}")
def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    model_arg = sys.argv[1].lower()
    time_arg  = sys.argv[2].lower()

    if time_arg not in TIME_OF_DAY:
        print(f" Невідомий час доби: {time_arg}")
        sys.exit(1)

    queries = load_queries()

    if model_arg == "all":
        print(f"  Запуск ВСІХ {len(MODELS)} моделей.")
        confirm = input("Продовжити? (y/n): ")
        if confirm.lower() != "y":
            sys.exit(0)

        for model_key in MODELS:
            data = test_one_model(model_key, time_arg, queries)
            save_results(data, time_arg, model_key)

    elif model_arg in MODELS:
        data = test_one_model(model_arg, time_arg, queries)
        save_results(data, time_arg, model_arg)

    else:
        print(f" Невідома модель: {model_arg}")
        sys.exit(1)

    print("\n Готово.")

if __name__ == "__main__":
    main()
