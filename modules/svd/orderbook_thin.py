def detect_thin_zones(orderbook: dict, top_levels: int = 20, gap_factor: float = 0.3):
    """
    Находит "дыры" в стакане (thin zones) рядом с ценой.

    Args:
        orderbook: {"bids": [(price, vol), ...], "asks": [...]}
        top_levels: сколько уровней анализировать
        gap_factor: порог, насколько объем должен быть меньше среднего

    Returns:
        {
            "thin_above": (price, vol) | None,
            "thin_below": (price, vol) | None
        }
    """
    if not orderbook or "bids" not in orderbook or "asks" not in orderbook:
        return {"thin_above": None, "thin_below": None}

    bids = orderbook.get("bids", [])[:top_levels]
    asks = orderbook.get("asks", [])[:top_levels]

    # Средние объемы по сторонам
    avg_bid = sum(v for _, v in bids) / len(bids) if bids else 0
    avg_ask = sum(v for _, v in asks) / len(asks) if asks else 0

    thin_above = None
    thin_below = None

    if asks and avg_ask > 0:
        for p, v in asks:
            if v < avg_ask * gap_factor:
                thin_above = (p, v)
                break

    if bids and avg_bid > 0:
        for p, v in bids:
            if v < avg_bid * gap_factor:
                thin_below = (p, v)
                break

    return {"thin_above": thin_above, "thin_below": thin_below}

