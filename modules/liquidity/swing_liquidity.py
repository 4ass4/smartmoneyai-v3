# modules/liquidity/swing_liquidity.py

# Используем свинги как ориентир стопов толпы.


def detect_swing_liquidity(market_structure):
    """
    Liquidity над/под свингами.
    """

    highs = market_structure["swings"]["highs"]
    lows = market_structure["swings"]["lows"]

    swing_liq = []

    for h in highs:
        swing_liq.append({
            "type": "buy_stops",
            "price": h["price"],
            "origin": "swing_high"
        })

    for l in lows:
        swing_liq.append({
            "type": "sell_stops",
            "price": l["price"],
            "origin": "swing_low"
        })

    return swing_liq

