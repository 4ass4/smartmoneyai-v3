# modules/svd/aggression.py

def detect_aggression(trades):
    """
    Агрессия = кто бьёт маркетом чаще и больше.
    """
    if not trades or not isinstance(trades, list):
        return {"buy_aggression": 0, "sell_aggression": 0}

    buy_aggr = 0
    sell_aggr = 0

    for t in trades:
        if not isinstance(t, dict):
            continue
        try:
            side = t.get("side", "")
            volume = float(t.get("volume", 0))
            if side == "buy":
                buy_aggr += volume
            else:
                sell_aggr += volume
        except (KeyError, ValueError, TypeError):
            continue

    return {
        "buy_aggression": buy_aggr,
        "sell_aggression": sell_aggr
    }

