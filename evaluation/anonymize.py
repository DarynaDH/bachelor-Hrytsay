import json
import random
import sys
from pathlib import Path

#анонімізує відповіді моделей перед оцінкою суддею
def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    time_of_day = sys.argv[1].lower()

    base = Path(__file__).parent
    responses_dir = base / "responses"
    out_dir = base / "anonymized"
    out_dir.mkdir(exist_ok=True)

    files = sorted(f for f in responses_dir.glob(f"responses_{time_of_day}_*.json")
                   if not f.name.startswith("with_costs_"))
    if not files:
        print(f"Не знайдено файлів responses_{time_of_day}_*.json")
        sys.exit(1)

    print(f"Знайдено {len(files)} файл(ів) для часу '{time_of_day}'")

    all_responses = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for r in data["results"]:
            if not r.get("ok") or r.get("anomaly", False):
                continue

            all_responses.append({
                "model_key":      data["model_key"],
                "query_id":       r["query_id"],
                "category":       r["category"],
                "query_text":     r["query_text"],
                "response_text":  r["response_text"],
            })

    if not all_responses:
        print("Немає валідних відповідей")
        sys.exit(1)

    print(f"   Зібрано {len(all_responses)} відповідей")

    random.seed(42)
    random.shuffle(all_responses)

    anonymized = []
    mapping = []
    for i, r in enumerate(all_responses, 1):
        anon_id = f"resp_{i:03d}"
        anonymized.append({
            "anon_id":       anon_id,
            "query_id":      r["query_id"],
            "category":      r["category"],
            "query_text":    r["query_text"],
            "response_text": r["response_text"],
        })
        mapping.append({
            "anon_id":   anon_id,
            "model_key": r["model_key"],
            "query_id":  r["query_id"],
        })

    anon_path    = out_dir / f"{time_of_day}_for_judge.json"
    mapping_path = out_dir / f"{time_of_day}_mapping.json"

    with open(anon_path, "w", encoding="utf-8") as f:
        json.dump({"time_of_day": time_of_day, "responses": anonymized}, f, ensure_ascii=False, indent=2)

    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump({"time_of_day": time_of_day, "mapping": mapping}, f, ensure_ascii=False, indent=2)

    print(f"\n Для судді: {anon_path}")
    print(f" Мапа:      {mapping_path}")


if __name__ == "__main__":
    main()
