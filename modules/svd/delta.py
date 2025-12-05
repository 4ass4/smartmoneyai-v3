# modules/svd/delta.py

def compute_delta(trades):
    """
    Дельта = объём по маркет-бай - объём по маркет-селл.
    """
    if not trades or not isinstance(trades, list):
        return 0

    buy_vol = 0
    sell_vol = 0

    for t in trades:
        if not isinstance(t, dict):
            continue
        try:
            side = t.get("side", "")
            volume = float(t.get("volume", 0))
            if side == "buy":
                buy_vol += volume
            else:
                sell_vol += volume
        except (KeyError, ValueError, TypeError):
            continue

    return buy_vol - sell_vol

