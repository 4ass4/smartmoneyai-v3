# modules/liquidity/detector_stops.py

def detect_stop_clusters(orderbook, price):
    """
    Поиск скоплений ликвидности:
    - стоп-лоссы
    - ликвидации
    - зоны, где стоит толпа

    Наша логика минималистична:
    Если рядом с ценой на 0.1–0.5% есть плотные объёмы — там стоят стопы.
    """

    clusters = {"above": [], "below": []}

    for ask_price, volume in orderbook["asks"]:
        if ask_price <= price * 1.005:      # до +0.5%
            if volume > orderbook["avg_ask"] * 3:
                clusters["above"].append((ask_price, volume))

    for bid_price, volume in orderbook["bids"]:
        if bid_price >= price * 0.995:      # до -0.5%
            if volume > orderbook["avg_bid"] * 3:
                clusters["below"].append((bid_price, volume))

    return clusters

