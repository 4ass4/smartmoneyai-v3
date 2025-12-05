def compute_orderbook_imbalance(orderbook: dict, top_levels: int = 5):
    """
    Рассчитывает дисбаланс стакана по верхним уровням.

    Args:
        orderbook: словарь {"bids": [(price, volume), ...], "asks": [...]}
        top_levels: количество уровней для анализа

    Returns:
        dict с дисбалансом:
        {
            "bid_vol": float,
            "ask_vol": float,
            "imbalance": float,  # bid_vol / max(ask_vol, 1e-6)
            "side": "bid"/"ask"/"neutral"
        }
    """
    if not orderbook or "bids" not in orderbook or "asks" not in orderbook:
        return {"bid_vol": 0, "ask_vol": 0, "imbalance": 1.0, "side": "neutral"}

    bids = orderbook.get("bids", [])[:top_levels]
    asks = orderbook.get("asks", [])[:top_levels]

    bid_vol = sum(v for _, v in bids)
    ask_vol = sum(v for _, v in asks)

    if ask_vol == 0 and bid_vol == 0:
        return {"bid_vol": 0, "ask_vol": 0, "imbalance": 1.0, "side": "neutral"}

    imbalance = bid_vol / max(ask_vol, 1e-6)

    if imbalance > 1.2:
        side = "bid"
    elif imbalance < 0.8:
        side = "ask"
    else:
        side = "neutral"

    return {
        "bid_vol": bid_vol,
        "ask_vol": ask_vol,
        "imbalance": imbalance,
        "side": side
    }

