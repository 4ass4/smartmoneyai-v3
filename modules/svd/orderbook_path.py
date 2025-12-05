def compute_path_cost(orderbook: dict, current_price: float, depth_levels: int = 20):
    """
    Приближенный "стоимостной" путь вверх/вниз:
    - интеграл объёмов в стакане на первых depth_levels
    - вес по дистанции от текущей цены

    Возвращает:
        {"up": cost_up, "down": cost_down}
    """
    if not orderbook or current_price is None or current_price == 0:
        return {"up": 0.0, "down": 0.0}

    bids = orderbook.get("bids", [])[:depth_levels]
    asks = orderbook.get("asks", [])[:depth_levels]

    cost_up = 0.0
    cost_down = 0.0

    for price, vol in asks:
        if price <= 0:
            continue
        dist = max(price - current_price, 0)
        cost_up += vol * (dist / current_price)

    for price, vol in bids:
        if price <= 0:
            continue
        dist = max(current_price - price, 0)
        cost_down += vol * (dist / current_price)

    return {"up": cost_up, "down": cost_down}

