def detect_trend(swings):
    """
    Простой метод определения тренда по последним свингам.
    HH + HL → бычий
    LH + LL → медвежий
    иначе → боковик
    """

    highs = swings["highs"]
    lows = swings["lows"]

    if len(highs) < 2 or len(lows) < 2:
        return "unknown"

    # Higher Highs?
    hh = highs[-1]["price"] > highs[-2]["price"]
    # Higher Lows?
    hl = lows[-1]["price"] > lows[-2]["price"]

    # Lower Highs?
    lh = highs[-1]["price"] < highs[-2]["price"]
    # Lower Lows?
    ll = lows[-1]["price"] < lows[-2]["price"]

    if hh and hl:
        return "bullish"
    if lh and ll:
        return "bearish"

    return "range"

