import json
import sys
from pathlib import Path
from collections import defaultdict

#об'єднує оцінки з реальними назвами моделей
def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    time_of_day = sys.argv[1].lower()
    base = Path(__file__).parent

    scores_path  = base / "anonymized" / f"{time_of_day}_scores.json"
    mapping_path = base / "anonymized" / f"{time_of_day}_mapping.json"

    if not scores_path.exists():
        print(f" Не знайдено {scores_path}")
        sys.exit(1)
    if not mapping_path.exists():
        print(f" Не знайдено {mapping_path}")
        sys.exit(1)

    with open(scores_path, "r", encoding="utf-8") as f:
        scores_data = json.load(f)
    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping_data = json.load(f)

    anon_to_model = {m["anon_id"]: m["model_key"] for m in mapping_data["mapping"]}

    merged = []
    for s in scores_data["scores"]:
        merged.append({
            **s,
            "model_key": anon_to_model.get(s["anon_id"], "unknown"),
        })

    by_model = defaultdict(list)
    by_model_category = defaultdict(lambda: defaultdict(list))

    for m in merged:
        if m.get("rating") is None:
            continue
        by_model[m["model_key"]].append(m["rating"])
        by_model_category[m["model_key"]][m["category"]].append(m["rating"])

    print(f"\n{'=' * 60}")
    print(f"СЕРЕДНІ ОЦІНКИ ПО МОДЕЛЯХ (шкала 1-10)")
    print(f"{'=' * 60}")
    print(f"{'Модель':<10} {'Сер. оцінка':<14} {'Оцінок':<8} {'Мін':<6} {'Макс':<6}")
    print("-" * 50)

    summary = {}
    for model_key in sorted(by_model.keys()):
        ratings = by_model[model_key]
        avg = sum(ratings) / len(ratings)
        summary[model_key] = {
            "avg_rating":   round(avg, 2),
            "num_ratings":  len(ratings),
            "min_rating":   min(ratings),
            "max_rating":   max(ratings),
            "by_category": {
                cat: round(sum(r) / len(r), 2)
                for cat, r in by_model_category[model_key].items()
            },
        }
        print(f"{model_key:<10} {round(avg, 2):<14} {len(ratings):<8} {min(ratings):<6} {max(ratings):<6}")

    print(f"\n{'=' * 60}")
    print("ОЦІНКИ ПО КАТЕГОРІЯХ:")
    print(f"{'=' * 60}")
    categories = sorted(set(c for m in by_model_category.values() for c in m.keys()))
    header = f"{'Модель':<10} " + " ".join(f"{c:<12}" for c in categories)
    print(header)
    print("-" * len(header))
    for model_key in sorted(by_model.keys()):
        row = f"{model_key:<10} "
        for cat in categories:
            ratings = by_model_category[model_key].get(cat, [])
            if ratings:
                avg = sum(ratings) / len(ratings)
                row += f"{round(avg, 2):<12} "
            else:
                row += f"{'—':<12} "
        print(row)

    out_path = base / "quality_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "time_of_day": time_of_day,
            "by_model": summary,
            "detailed": merged,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n {out_path}")


if __name__ == "__main__":
    main()
