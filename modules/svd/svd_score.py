# modules/svd/svd_score.py

def svd_confidence_score(delta, absorption, aggression, velocity, dom_imbalance=None, bucket_metrics=None):
    """
    Финальный Confidence Score SVD: 0–10
    Добавлены:
      - дисбаланс стакана (DOM)
      - краткосрочные бакеты сделок (delta/velocity)
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

    # 5. Дисбаланс стакана (DOM)
    if dom_imbalance:
        imb = dom_imbalance.get("imbalance", 1)
        side = dom_imbalance.get("side", "neutral")
        if side != "neutral":
            if imb > 1.5 or imb < 0.67:
                score += 1.0
            elif imb > 1.2 or imb < 0.83:
                score += 0.5

    # 6. Краткосрочные бакеты сделок
    if bucket_metrics:
        last_delta = abs(bucket_metrics.get("last_bucket_delta", 0))
        last_vel = bucket_metrics.get("last_bucket_velocity", 0)
        if last_delta > 5000:
            score += 0.5
        if last_vel > 10:
            score += 0.5

    return min(score, 10)

