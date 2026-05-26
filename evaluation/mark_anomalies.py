import json
from pathlib import Path

#Позначає аномальні відповіді (>6000 токенів output).
ANOMALY_THRESHOLD = 6000

def is_anomaly(result):
    tokens = result.get("completion_tokens") or 0
    return tokens > ANOMALY_THRESHOLD
def process_file(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    found = []
    for r in data["results"]:
        anomaly = is_anomaly(r)
        r["anomaly"] = anomaly
        if anomaly:
            found.append({
                "file":              path.name,
                "query_id":          r["query_id"],
                "completion_tokens": r["completion_tokens"],
                "elapsed_seconds":   r["elapsed_seconds"],
            })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return found
def main():
    base = Path(__file__).parent
    responses_dir = base / "responses"

    if not responses_dir.exists():
        print(f" Папка {responses_dir} не існує.")
        return

    files = sorted(responses_dir.glob("responses_*.json"))
    if not files:
        print(" Немає файлів з відповідями.")
        return

    print(f" Перевіряю {len(files)} файл(ів) (поріг: {ANOMALY_THRESHOLD} токенів)\n")

    all_anomalies = []
    for path in files:
        anomalies = process_file(path)
        all_anomalies.extend(anomalies)

    if not all_anomalies:
        print(" Аномалій не знайдено.")
    else:
        print(f"  Знайдено {len(all_anomalies)} аномалій:\n")
        print(f"{'Файл':<40} {'Запит':<8} {'Токенів':<10} {'Час, с':<8}")
        print("-" * 70)
        for a in all_anomalies:
            print(f"{a['file']:<40} {a['query_id']:<8} {a['completion_tokens']:<10} {a['elapsed_seconds']:<8}")


if __name__ == "__main__":
    main()
