# modules/liquidity/liquidity_direction.py

# Это ключ — определяет, куда выгодно двигать цену.


def detect_liquidity_direction(stop_clusters, swing_liq, ath_atl, df):
    """
    Анализируем, где больше ликвидности:
    - стопы покупателей → тянуть цену ВВЕРХ (чтобы собрать)
    - стопы продавцов → тянуть ВНИЗ
    """

    up_liq = 0
    down_liq = 0
    current_price = df['close'].iloc[-1]

    # стоп-кластеры
    for c in stop_clusters:
        if c["type"] == "buy_stops" and c["price"] > current_price:
            up_liq += 1
        if c["type"] == "sell_stops" and c["price"] < current_price:
            down_liq += 1

    # свинги
    for s in swing_liq:
        if s["type"] == "buy_stops" and s["price"] > current_price:
            up_liq += 1
        if s["type"] == "sell_stops" and s["price"] < current_price:
            down_liq += 1

    # ATH / ATL
    if ath_atl["ath"]["price"] > current_price:
        up_liq += 1
    if ath_atl["atl"]["price"] < current_price:
        down_liq += 1

    # Итоговое направление
    if up_liq > down_liq:
        return {"direction": "up", "reason": "above_price_liquidity"}
    elif down_liq > up_liq:
        return {"direction": "down", "reason": "below_price_liquidity"}
    else:
        return {"direction": "neutral", "reason": "balanced"}

