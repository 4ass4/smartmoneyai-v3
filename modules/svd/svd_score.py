# modules/svd/svd_score.py

def svd_confidence_score(delta, absorption, aggression, velocity):
    """
    Финальный Confidence Score SVD: 0–10
    """

    score = 0

    # 1. Дельта (адаптивные пороги в зависимости от объема)
    delta_abs = abs(delta)
    if delta_abs > 100000:
        score += 3
    elif delta_abs > 50000:
        score += 2.5
    elif delta_abs > 20000:
        score += 2
    elif delta_abs > 5000:
        score += 1
    elif delta_abs > 0:
        score += 0.5

    # 2. Поглощение
    if absorption.get("absorbing"):
        score += 3

    # 3. Агрессия (более гибкие пороги)
    buy_aggr = aggression.get("buy_aggression", 0)
    sell_aggr = aggression.get("sell_aggression", 0)
    total_aggr = buy_aggr + sell_aggr
    
    if total_aggr > 0:
        if buy_aggr > sell_aggr * 1.5:
            score += 2
        elif sell_aggr > buy_aggr * 1.5:
            score += 2
        elif buy_aggr > sell_aggr * 1.2:
            score += 1
        elif sell_aggr > buy_aggr * 1.2:
            score += 1

    # 4. Скорость сделок (адаптивные пороги)
    vel = velocity.get("velocity", 0)
    if vel > 100:
        score += 3
    elif vel > 50:
        score += 2
    elif vel > 20:
        score += 1.5
    elif vel > 5:
        score += 1
    elif vel > 0:
        score += 0.5

    return min(score, 10)

