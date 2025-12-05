def detect_range(swings, df):
    """
    Простой боковой диапазон: 
    - последние 3 свинга хай и лоу в пределах ~1.5%
    """

    highs = swings["highs"]
    lows = swings["lows"]

    if len(highs) < 2 or len(lows) < 2:
        return {"in_range": False}

    hi1, hi2 = highs[-1]["price"], highs[-2]["price"]
    lo1, lo2 = lows[-1]["price"], lows[-2]["price"]

    top_variation = abs(hi1 - hi2) / hi2
    bottom_variation = abs(lo1 - lo2) / lo2

    if top_variation < 0.015 and bottom_variation < 0.015:
        return {
            "in_range": True,
            "top": max(hi1, hi2),
            "bottom": min(lo1, lo2)
        }

    return {"in_range": False}

