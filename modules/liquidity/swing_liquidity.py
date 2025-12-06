# modules/liquidity/swing_liquidity.py

# Используем свинги как ориентир стопов толпы.

from modules.utils.time_decay import calculate_time_decay
import time


def detect_swing_liquidity(market_structure, apply_time_decay=True):
    """
    Liquidity над/под свингами.
    
    Args:
        market_structure: данные от MarketStructureEngine
        apply_time_decay: применять ли time-decay к старым свингам
    """

    highs = market_structure["swings"]["highs"]
    lows = market_structure["swings"]["lows"]

    swing_liq = []
    current_ts = int(time.time() * 1000)

    for h in highs:
        swing_ts = h.get("timestamp")
        decay_weight = calculate_time_decay(swing_ts, current_ts) if apply_time_decay and swing_ts else 1.0
        swing_liq.append({
            "type": "buy_stops",
            "price": h["price"],
            "origin": "swing_high",
            "timestamp": swing_ts,
            "decay_weight": decay_weight
        })

    for l in lows:
        swing_ts = l.get("timestamp")
        decay_weight = calculate_time_decay(swing_ts, current_ts) if apply_time_decay and swing_ts else 1.0
        swing_liq.append({
            "type": "sell_stops",
            "price": l["price"],
            "origin": "swing_low",
            "timestamp": swing_ts,
            "decay_weight": decay_weight
        })

    return swing_liq

