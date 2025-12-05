# modules/liquidity/scoring.py

def score_liquidity_map(stops, heatmap, imbalance):
    """
    Система скоринга для Confidence:
    0–10 баллов.
    """

    score = 0

    # 1) Кластеры стопов — сильный сигнал
    score += min(len(stops["above"]) + len(stops["below"]), 4)

    # 2) Сильные уровни лимиток
    score += min(len(heatmap["strong_levels"]), 3)

    # 3) Сильный дисбаланс
    if imbalance["up"] > imbalance["down"] * 1.3:
        score += 3
    elif imbalance["down"] > imbalance["up"] * 1.3:
        score += 3

    return min(score, 10)

