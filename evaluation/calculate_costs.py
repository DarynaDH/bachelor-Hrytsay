import json
from pathlib import Path
from collections import defaultdict

#підрахунок вартості зібраних відповідей
PRICING = {
    "claude": {"input": 5.00,  "output": 25.00},
    "gemini": {"input": 2.00,  "output": 12.00},
    "gpt":    {"input": 2.50,  "output": 15.00},
    "glm":    {"input": 0.60,  "output":  1.92},
    "qwen":   {"input": 0.39,  "output":  2.34},
    "grok":   {"input": 1.25,  "output":  2.50},
    "kimi":   {"input": 0.40,  "output":  1.90},
}


def calc_cost(model_key, prompt_tokens, completion_tokens):
    if model_key not in PRICING:
        return 0.0
    p = PRICING[model_key]
    cost = (
        (prompt_tokens or 0) / 1_000_000 * p["input"]
        + (completion_tokens or 0) / 1_000_000 * p["output"]
    )
    return round(cost, 6)


def process_file(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    model_key = data["model_key"]
    time_of_day = data["time_of_day"]
    results = data["results"]

    enriched = []
    for r in results:
        cost = calc_cost(model_key, r.get("prompt_tokens"), r.get("completion_tokens"))
        enriched.append({**r, "cost_usd": cost})

    normal = [r for r in enriched if r["ok"] and not r.get("anomaly", False)]
    anomalies = [r for r in enriched if r.get("anomaly", False)]

    total_cost_normal = sum(r["cost_usd"] for r in normal)
    avg_time = sum(r["elapsed_seconds"] for r in normal) / len(normal) if normal else 0
    avg_cost = total_cost_normal / len(normal) if normal else 0
    total_cost_all = sum(r["cost_usd"] for r in enriched)

    return {
        "model_key": model_key,
        "time_of_day": time_of_day,
        "total_queries": len(results),
        "successful": sum(1 for r in results if r["ok"]),
        "anomalies": len(anomalies),
        "normal_used": len(normal),
        "total_cost_normal_usd": round(total_cost_normal, 4),
        "total_cost_all_usd": round(total_cost_all, 4),
        "avg_cost_per_query_usd": round(avg_cost, 6),
        "avg_time_seconds": round(avg_time, 2),
        "results": enriched,
    }


def main():
    base = Path(__file__).parent
    responses_dir = base / "responses"

    if not responses_dir.exists():
        print(f" Папка {responses_dir} не існує.")
        return

    files = sorted(f for f in responses_dir.glob("responses_*.json")
                   if not f.name.startswith("with_costs_"))
    if not files:
        print("Немає файлів з відповідями.")
        return

    print(f"Знайдено {len(files)} файл(ів)\n")

    all_data = []
    summary_by_model = defaultdict(lambda: {
        "times": [], "costs_per_query": [], "total_cost": 0.0, "anomalies": 0,
    })

    for path in files:
        result = process_file(path)
        all_data.append(result)

        out_detailed = path.parent / f"with_costs_{path.name}"
        with open(out_detailed, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        m = summary_by_model[result["model_key"]]
        m["times"].append(result["avg_time_seconds"])
        m["costs_per_query"].append(result["avg_cost_per_query_usd"])
        m["total_cost"] += result["total_cost_all_usd"]
        m["anomalies"] += result["anomalies"]

    print(f"{'Модель':<10} {'Час дня':<10} {'Норм/Аном':<12} {'Сер. час':<12} {'Сер. USD':<14} {'Всього USD':<12}")
    print("-" * 80)
    for r in all_data:
        norm_anom = f"{r['normal_used']}/{r['anomalies']}"
        print(f"{r['model_key']:<10} {r['time_of_day']:<10} {norm_anom:<12} "
              f"{r['avg_time_seconds']:<12} {r['avg_cost_per_query_usd']:<14} {r['total_cost_all_usd']:<12}")

    print("\n" + "=" * 80)
    print("ПІДСУМОК ПО МОДЕЛЯХ:")
    print("=" * 80)
    print(f"{'Модель':<10} {'Сер. час, с':<14} {'Сер. USD/запит':<18} {'Всього USD':<12} {'Аномалій':<10}")
    print("-" * 80)

    final_summary = {}
    grand_total = 0.0
    for model_key, m in summary_by_model.items():
        avg_time = sum(m["times"]) / len(m["times"]) if m["times"] else 0
        avg_cost = sum(m["costs_per_query"]) / len(m["costs_per_query"]) if m["costs_per_query"] else 0
        total = m["total_cost"]

        final_summary[model_key] = {
            "avg_time_seconds": round(avg_time, 2),
            "avg_cost_per_query_usd": round(avg_cost, 6),
            "total_cost_usd": round(total, 4),
            "num_runs": len(m["times"]),
            "anomalies_total": m["anomalies"],
        }

        grand_total += total
        print(f"{model_key:<10} {round(avg_time, 2):<14} {round(avg_cost, 6):<18} {round(total, 4):<12} {m['anomalies']:<10}")

    print("-" * 80)
    print(f" ЗАГАЛЬНІ ВИТРАТИ: ${round(grand_total, 4)}\n")

    out_path = base / "costs_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "by_run": all_data,
            "by_model": final_summary,
            "total_cost_usd": round(grand_total, 4),
        }, f, ensure_ascii=False, indent=2)

    print(f"Підсумок: {out_path}")


if __name__ == "__main__":
    main()
