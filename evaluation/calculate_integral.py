
#розрахунок інтегрального показника моделей.

#Метрики:
    #Якість        — оцінка LLM-судді за рубрикою (шкала 1-10)
    #Час відповіді — середній час у секундах (менше = краще)
    #Вартість      — середня вартість запиту в USD (менше = краще)

#Формула нормалізації:
    #Для "більше = краще": N = (x - min) / (max - min)
    #Для "менше = краще":  N = (max - x) / (max - min)

#Ваги: якість 0.50, час 0.30, вартість 0.20.

import json
from pathlib import Path
from collections import defaultdict

WEIGHTS = {"quality": 0.50, "time": 0.30, "cost": 0.20}

MODEL_NAMES = {
    "claude": "Claude Opus 4.6",
    "gemini": "Gemini 3.1 Pro",
    "glm":    "GLM-5",
    "gpt":    "GPT-5.4",
    "grok":   "Grok 4.20",
    "kimi":   "Kimi K2.5",
    "qwen":   "Qwen3.5-397B",
}
def normalize_higher(values):
    vals = list(values.values())
    mn, mx = min(vals), max(vals)
    if mx == mn:
        return {k: 1.0 for k in values}
    return {k: (v - mn) / (mx - mn) for k, v in values.items()}


def normalize_lower(values):
    vals = list(values.values())
    mn, mx = min(vals), max(vals)
    if mx == mn:
        return {k: 1.0 for k in values}
    return {k: (mx - v) / (mx - mn) for k, v in values.items()}

def load_judge_scores(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    mapping_path = path.parent / f"{data['time_of_day']}_mapping.json"
    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping_data = json.load(f)
    anon_to_model = {m["anon_id"]: m["model_key"] for m in mapping_data["mapping"]}

    by_model = defaultdict(list)
    for s in data["scores"]:
        if s.get("rating") is None:
            continue
        model = anon_to_model.get(s["anon_id"])
        if model:
            by_model[model].append(s["rating"])

    return {k: sum(v) / len(v) for k, v in by_model.items()}
def compute_integral(quality, time_resp, cost):
    n_q = normalize_higher(quality)
    n_t = normalize_lower(time_resp)
    n_c = normalize_lower(cost)

    result = {}
    for k in quality:
        score = (
            WEIGHTS["quality"] * n_q[k]
            + WEIGHTS["time"]  * n_t[k]
            + WEIGHTS["cost"]  * n_c[k]
        )
        result[k] = round(score, 3)
    return result

def spearman_corr(rankings_a, rankings_b):
    keys = list(rankings_a.keys())
    rank_a = {k: i for i, k in enumerate(sorted(keys, key=lambda x: -rankings_a[x]))}
    rank_b = {k: i for i, k in enumerate(sorted(keys, key=lambda x: -rankings_b[x]))}
    n = len(keys)
    d2 = sum((rank_a[k] - rank_b[k]) ** 2 for k in keys)
    return round(1 - 6 * d2 / (n * (n ** 2 - 1)), 3)


def main():
    base = Path(__file__).parent
    anon_dir = base / "anonymized"

    gpt_path    = anon_dir / "evening_scores_gpt.json"
    claude_path = anon_dir / "evening_scores_claude.json"
    costs_path  = base / "costs_summary.json"

    for p in [gpt_path, claude_path, costs_path]:
        if not p.exists():
            print(f" Не знайдено {p}")
            return

    quality_gpt    = load_judge_scores(gpt_path)
    quality_claude = load_judge_scores(claude_path)

    with open(costs_path, "r", encoding="utf-8") as f:
        costs_data = json.load(f)
    time_resp = {k: v["avg_time_seconds"] for k, v in costs_data["by_model"].items()}
    cost      = {k: v["avg_cost_per_query_usd"] for k, v in costs_data["by_model"].items()}

    models = sorted(set(quality_gpt) & set(quality_claude) & set(time_resp) & set(cost))

    q_gpt    = {m: quality_gpt[m] for m in models}
    q_claude = {m: quality_claude[m] for m in models}
    q_avg    = {m: (q_gpt[m] + q_claude[m]) / 2 for m in models}
    t        = {m: time_resp[m] for m in models}
    c        = {m: cost[m] for m in models}

    int_gpt    = compute_integral(q_gpt, t, c)
    int_claude = compute_integral(q_claude, t, c)
    int_avg    = compute_integral(q_avg, t, c)

    corr = spearman_corr(int_gpt, int_claude)

    print()
    print("=" * 95)
    print("  СИРІ ДАНІ")
    print("=" * 95)
    print(f"{'Модель':<18} {'Якість GPT':<12} {'Якість Claude':<15} {'Сер. якість':<13} {'Час, с':<10} {'Варт. USD':<12}")
    print("-" * 95)
    for m in sorted(models, key=lambda x: -int_avg[x]):
        print(f"{MODEL_NAMES.get(m, m):<18} {round(q_gpt[m], 2):<12} {round(q_claude[m], 2):<15} "
              f"{round(q_avg[m], 2):<13} {round(t[m], 2):<10} {round(c[m], 5):<12}")

    print()
    print("=" * 95)
    print(f"  ІНТЕГРАЛЬНИЙ ПОКАЗНИК (ваги: якість={WEIGHTS['quality']}, час={WEIGHTS['time']}, варт={WEIGHTS['cost']})")
    print("=" * 95)
    print(f"{'Місце':<6} {'Модель':<18} {'GPT-суддя':<12} {'Claude-суддя':<14} {'Усереднено':<12}")
    print("-" * 95)
    for i, m in enumerate(sorted(models, key=lambda x: -int_avg[x]), 1):
        print(f"{i:<6} {MODEL_NAMES.get(m, m):<18} {int_gpt[m]:<12} {int_claude[m]:<14} {int_avg[m]:<12}")

    print()
    print("=" * 95)
    print("  КРОСС-ВАЛІДАЦІЯ СУДДІВ")
    print("=" * 95)
    rank_gpt    = sorted(models, key=lambda m: -int_gpt[m])
    rank_claude = sorted(models, key=lambda m: -int_claude[m])
    print(f"GPT-суддя:    {' > '.join(MODEL_NAMES.get(m, m) for m in rank_gpt)}")
    print(f"Claude-суддя: {' > '.join(MODEL_NAMES.get(m, m) for m in rank_claude)}")
    print()
    print(f" Кореляція Спірмена: {corr}")

    out_path = base / "integral_summary.json"
    summary = {
        "weights": WEIGHTS,
        "models": {
            m: {
                "name": MODEL_NAMES.get(m, m),
                "quality_gpt": round(q_gpt[m], 2),
                "quality_claude": round(q_claude[m], 2),
                "quality_avg": round(q_avg[m], 2),
                "time_seconds": round(t[m], 2),
                "cost_usd": round(c[m], 5),
                "integral_gpt": int_gpt[m],
                "integral_claude": int_claude[m],
                "integral_avg": int_avg[m],
            }
            for m in models
        },
        "ranking_avg": sorted(models, key=lambda m: -int_avg[m]),
        "spearman_correlation": corr,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    winner = sorted(models, key=lambda m: -int_avg[m])[0]
    print()
    print(f" {out_path}")
    print(f" Лідер: {MODEL_NAMES.get(winner, winner)} ({int_avg[winner]})")


if __name__ == "__main__":
    main()
