# modules/liquidity/liquidity_direction.py

# Это ключ — определяет, куда выгодно двигать цену.


def detect_liquidity_direction(stop_clusters, swing_liq, ath_atl, df):
    """
    Анализируем, где больше ликвидности:
    - стопы покупателей → тянуть цену ВВЕРХ (чтобы собрать)
    - стопы продавцов → тянуть ВНИЗ
    
    Учитываем decay_weight для старых уровней
    """

    up_liq = 0.0
    down_liq = 0.0
    current_price = df['close'].iloc[-1]

    # стоп-кластеры (с учётом decay_weight)
    for c in stop_clusters:
        weight = c.get("decay_weight", 1.0)
        if c["type"] == "buy_stops" and c["price"] > current_price:
            up_liq += weight
        if c["type"] == "sell_stops" and c["price"] < current_price:
            down_liq += weight

    # свинги (с учётом decay_weight)
    for s in swing_liq:
        weight = s.get("decay_weight", 1.0)
        if s["type"] == "buy_stops" and s["price"] > current_price:
            up_liq += weight
        if s["type"] == "sell_stops" and s["price"] < current_price:
            down_liq += weight

    # ATH / ATL (всегда полный вес, т.к. глобальные уровни)
    if ath_atl["ath"]["price"] > current_price:
        up_liq += 1.0
    if ath_atl["atl"]["price"] < current_price:
        down_liq += 1.0

    # Итоговое направление
    if up_liq > down_liq * 1.1:  # небольшой гистерезис для стабильности
        return {"direction": "up", "reason": "above_price_liquidity", "up_weight": up_liq, "down_weight": down_liq}
    elif down_liq > up_liq * 1.1:
        return {"direction": "down", "reason": "below_price_liquidity", "up_weight": up_liq, "down_weight": down_liq}
    else:
        return {"direction": "neutral", "reason": "balanced", "up_weight": up_liq, "down_weight": down_liq}

