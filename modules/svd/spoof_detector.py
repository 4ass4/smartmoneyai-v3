def detect_spoof_wall(orderbook: dict, current_price: float, proximity: float = 0.002, wall_mult: float = 4.0, top_levels: int = 10):
    """
    Простая эвристика "спуф-стенки": крупная заявка близко к цене.

    Args:
        orderbook: {"bids": [(price, vol), ...], "asks": [...]}
        current_price: текущая цена
        proximity: доля (0.2%) от цены для учета уровня как "близкий"
        wall_mult: насколько объем должен превышать средний по стороне
        top_levels: сколько уровней анализировать

    Returns:
        {
            "side": "bid"/"ask"/None,
            "price": float|None,
            "volume": float|None,
            "factor": float  # отношение к среднему объему
        }
    """
    if not orderbook or not current_price:
        return {"side": None, "price": None, "volume": None, "factor": 1.0}

    bids = orderbook.get("bids", [])[:top_levels]
    asks = orderbook.get("asks", [])[:top_levels]

    avg_bid = sum(v for _, v in bids) / len(bids) if bids else 0
    avg_ask = sum(v for _, v in asks) / len(asks) if asks else 0

    best = {"side": None, "price": None, "volume": None, "factor": 1.0}

    # Проверяем asks рядом с ценой
    for p, v in asks:
        if p <= current_price * (1 + proximity) and avg_ask > 0:
            factor = v / avg_ask
            if factor >= wall_mult and factor > best["factor"]:
                best = {"side": "ask", "price": p, "volume": v, "factor": factor}

    # Проверяем bids рядом с ценой
    for p, v in bids:
        if p >= current_price * (1 - proximity) and avg_bid > 0:
            factor = v / avg_bid
            if factor >= wall_mult and factor > best["factor"]:
                best = {"side": "bid", "price": p, "volume": v, "factor": factor}

    # Если не нашли — возвращаем пустой
    if best["side"] is None:
        return {"side": None, "price": None, "volume": None, "factor": 1.0}
    return best

