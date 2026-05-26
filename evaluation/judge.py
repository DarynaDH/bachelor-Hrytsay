import json
import os
import re
import sys
import time
from pathlib import Path
import requests
from dotenv import load_dotenv

#оцінювання анонімізованих відповідей 
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

JUDGE_MODEL = "openai/gpt-5.5"


# промпт зі статті Zheng et al. NeurIPS 2023, Figure 6 (Single Answer Grading)
JUDGE_PROMPT_TEMPLATE = """Виступи як неупереджений суддя і оціни якість відповіді AI-асистента на запит користувача, наведений нижче. Твоя оцінка має враховувати такі фактори: корисність (helpfulness), релевантність (relevance), точність (accuracy), глибина (depth), креативність (creativity) та рівень деталізації (level of detail) відповіді. Розпочни з короткого пояснення. Будь максимально об'єктивним. Після пояснення обов'язково оціни відповідь за шкалою від 1 до 10 у форматі [[оцінка]], наприклад: "Оцінка: [[5]]".

[Запит]
{question}

[Початок відповіді асистента]
{answer}
[Кінець відповіді асистента]"""


def parse_rating(text):
    m = re.search(r'\[\[(\d+(?:\.\d+)?)\]\]', text)
    if m:
        return float(m.group(1))
    return None


def judge_one(query, answer, timeout=60):
    prompt = JUDGE_PROMPT_TEMPLATE.format(question=query, answer=answer)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": JUDGE_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    start = time.time()
    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout)
        elapsed = time.time() - start
        resp.raise_for_status()
        data = resp.json()

        judge_text = data["choices"][0]["message"]["content"]
        rating = parse_rating(judge_text)

        return {
            "ok": True,
            "rating": rating,
            "judge_explanation": judge_text,
            "elapsed_seconds": round(elapsed, 2),
            "prompt_tokens": data.get("usage", {}).get("prompt_tokens"),
            "completion_tokens": data.get("usage", {}).get("completion_tokens"),
            "error": None,
        }
    except Exception as e:
        return {
            "ok": False, "rating": None, "judge_explanation": None,
            "elapsed_seconds": round(time.time() - start, 2),
            "prompt_tokens": None, "completion_tokens": None,
            "error": str(e),
        }


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    time_of_day = sys.argv[1].lower()
    base = Path(__file__).parent

    anon_path = base / "anonymized" / f"{time_of_day}_for_judge.json"
    if not anon_path.exists():
        print(f" Не знайдено {anon_path}")
        sys.exit(1)

    with open(anon_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    responses = data["responses"]
    total = len(responses)

    print(f"  Суддя: {JUDGE_MODEL}")
    print(f" Відповідей: {total}")
    print(f" Орієнтовно: ~${total * 0.05:.2f}")
    confirm = input("Продовжити? (y/n): ")
    if confirm.lower() != "y":
        return

    print()

    scores = []
    for i, r in enumerate(responses, 1):
        print(f"  [{i:3d}/{total}] {r['anon_id']} ({r['category']})... ", end="", flush=True)
        result = judge_one(r["query_text"], r["response_text"])

        if result["ok"]:
            print(f"✓ {result['rating']} | {result['elapsed_seconds']:.1f}с")
        else:
            print(f"✗ {result['error']}")

        scores.append({
            "anon_id":  r["anon_id"],
            "query_id": r["query_id"],
            "category": r["category"],
            **result,
        })

        if i % 10 == 0:
            out_path = base / "anonymized" / f"{time_of_day}_scores.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump({"time_of_day": time_of_day, "scores": scores}, f, ensure_ascii=False, indent=2)

    out_path = base / "anonymized" / f"{time_of_day}_scores.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"time_of_day": time_of_day, "scores": scores}, f, ensure_ascii=False, indent=2)

    print(f"\n {out_path}")


if __name__ == "__main__":
    main()
