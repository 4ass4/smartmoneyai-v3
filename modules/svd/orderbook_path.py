def compute_path_cost(
    orderbook: dict,
    current_price: float,
    depth_levels: int = 20,
    thin_zones: dict | None = None,
    volume_cap_factor: float = 5.0,
):
    """
    Приближенный "стоимостной" путь вверх/вниз:
    - интеграл объёмов в стакане на первых depth_levels
    - вес по дистанции от текущей цены

    Возвращает:
        {"up": cost_up, "down": cost_down}
    - volume_cap_factor: ограничение вклада одного уровня (в avg*factor)
    - thin_zones: если сверху/снизу тонко — удешевляем проход
    """
    if not orderbook or current_price is None or current_price == 0:
        return {"up": 0.0, "down": 0.0}

    bids = orderbook.get("bids", [])[:depth_levels]
    asks = orderbook.get("asks", [])[:depth_levels]
    avg_bid = orderbook.get("avg_bid", 0) or 0
    avg_ask = orderbook.get("avg_ask", 0) or 0

    cost_up = 0.0
    cost_down = 0.0

    for price, vol in asks:
        if price <= 0:
            continue
        dist = max(price - current_price, 0)
        cap = avg_ask * volume_cap_factor if avg_ask > 0 else vol
        cost_up += min(vol, cap) * (dist / current_price)

    for price, vol in bids:
        if price <= 0:
            continue
        dist = max(current_price - price, 0)
        cap = avg_bid * volume_cap_factor if avg_bid > 0 else vol
        cost_down += min(vol, cap) * (dist / current_price)

    # Удешевляем путь через тонкие зоны
    if thin_zones:
        if thin_zones.get("thin_above"):
            cost_up *= 0.7
        if thin_zones.get("thin_below"):
            cost_down *= 0.7

    return {"up": cost_up, "down": cost_down}

