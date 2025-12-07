# modules/liquidity/touch_detector.py

"""
Детектор касания уровней ликвидности
Проверяет был ли уровень коснут недавно (в последних N свечах)
"""


def detect_recent_touches(df, liquidity_levels, lookback=20, tolerance_pct=0.2):
    """
    Проверяет какие уровни ликвидности были коснуты недавно
    
    Args:
        df: OHLCV DataFrame
        liquidity_levels: список уровней для проверки
            [{"price": float, "type": "buy_stops/sell_stops"}, ...]
        lookback: сколько последних свечей проверять (default: 20)
        tolerance_pct: допуск касания в % (default: 0.2%)
    
    Returns:
        {
            "touched_levels": [{"price": X, "type": Y, "candles_ago": N}, ...],
            "untouched_levels": [{"price": X, "type": Y}, ...]
        }
    """
    if df is None or len(df) < 2 or not liquidity_levels:
        return {
            "touched_levels": [],
            "untouched_levels": liquidity_levels
        }
    
    touched = []
    untouched = []
    
    # Анализируем последние N свечей
    recent_candles = df.iloc[-min(lookback, len(df)):]
    
    for level in liquidity_levels:
        price = level.get("price", 0)
        level_type = level.get("type", "")
        
        if price == 0:
            continue
        
        # Порог касания
        tolerance = price * (tolerance_pct / 100)
        upper_bound = price + tolerance
        lower_bound = price - tolerance
        
        # Проверяем был ли касание в recent_candles
        was_touched = False
        touch_candle_idx = None
        
        for idx, candle in enumerate(recent_candles.itertuples()):
            # Проверяем касание high или low
            if level_type == "buy_stops":
                # Buy stops сверху - проверяем high
                if candle.high >= lower_bound:
                    was_touched = True
                    touch_candle_idx = len(recent_candles) - idx - 1  # Сколько свечей назад
                    break
            elif level_type == "sell_stops":
                # Sell stops снизу - проверяем low
                if candle.low <= upper_bound:
                    was_touched = True
                    touch_candle_idx = len(recent_candles) - idx - 1
                    break
            else:
                # Универсальная проверка (high или low в диапазоне)
                if lower_bound <= candle.high <= upper_bound or lower_bound <= candle.low <= upper_bound:
                    was_touched = True
                    touch_candle_idx = len(recent_candles) - idx - 1
                    break
        
        if was_touched:
            touched.append({
                "price": price,
                "type": level_type,
                "candles_ago": touch_candle_idx,
                "source": level.get("source", "unknown")
            })
        else:
            untouched.append(level)
    
    return {
        "touched_levels": touched,
        "untouched_levels": untouched
    }


def filter_touched_levels(liquidity_levels, touched_levels, min_cooldown_candles=10):
    """
    Фильтрует уровни ликвидности - удаляет недавно коснутые
    
    Args:
        liquidity_levels: полный список уровней
        touched_levels: список коснутых уровней (из detect_recent_touches)
        min_cooldown_candles: минимальное количество свечей после касания
                             для повторного учёта уровня
    
    Returns:
        list: отфильтрованные уровни (без недавно коснутых)
    """
    if not touched_levels:
        return liquidity_levels
    
    # Создаём set touched prices для быстрого поиска
    touched_prices = set()
    for touch in touched_levels:
        # Только если касание было недавно (< min_cooldown_candles)
        if touch.get("candles_ago", 999) < min_cooldown_candles:
            touched_prices.add(touch["price"])
    
    # Фильтруем
    filtered = []
    for level in liquidity_levels:
        price = level.get("price", 0)
        # Допуск 0.1% для сравнения float
        is_touched = any(abs(price - tp) / tp < 0.001 for tp in touched_prices)
        
        if not is_touched:
            filtered.append(level)
    
    return filtered

