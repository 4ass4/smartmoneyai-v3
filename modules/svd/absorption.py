# modules/svd/absorption.py

def detect_absorption(trades, orderbook):
    """
    Поглощение — это когда одна сторона маркет-ордеров бьёт в крупные лимитки,
    но цена НЕ двигается.
    """
    if not trades or not isinstance(trades, list) or len(trades) < 5:
        return {"absorbing": False, "side": None}
    
    if not orderbook or not isinstance(orderbook, dict):
        return {"absorbing": False, "side": None}

    try:
        # Проверяем, что последние сделки - это словари
        if not isinstance(trades[-1], dict) or not isinstance(trades[-5], dict):
            return {"absorbing": False, "side": None}
        
        last_price = float(trades[-1].get("price", 0))
        prev_price = float(trades[-5].get("price", 0))
        
        if last_price == 0 or prev_price == 0:
            return {"absorbing": False, "side": None}

        price_change = abs(last_price - prev_price) / prev_price

        # если большой объём маркетов, но цена почти не изменилась:
        big_trades = 0
        for t in trades[-10:]:
            if isinstance(t, dict):
                big_trades += float(t.get("volume", 0))

        avg_bid = float(orderbook.get("avg_bid", 0))
        avg_ask = float(orderbook.get("avg_ask", 0))
        
        if avg_bid == 0 or avg_ask == 0:
            return {"absorbing": False, "side": None}

        if price_change < 0.0005:  # < 0.05%
            if big_trades > avg_ask * 4:
                return {"absorbing": True, "side": "sell"}
            if big_trades > avg_bid * 4:
                return {"absorbing": True, "side": "buy"}

        return {"absorbing": False, "side": None}
    except (KeyError, ValueError, TypeError, IndexError) as e:
        # В случае ошибки возвращаем безопасное значение
        return {"absorbing": False, "side": None}

