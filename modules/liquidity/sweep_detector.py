def detect_sweep(df, lookback: int = 50, stop_prices_above=None, stop_prices_below=None):
    """
    Обнаружение ликвидити-свипа на последних свечах:
      - sweep_up: прокол недавних хайев с возвратом
      - sweep_down: прокол недавних лоев с возвратом

    Args:
        df: OHLCV DataFrame
        lookback: сколько предыдущих свечей брать для хай/лоу (default: 50 для истории)

    Дополнительно можно передать уровни стопов/ликвидности:
        stop_prices_above: список цен стопов выше (buy stops)
        stop_prices_below: список цен стопов ниже (sell stops)

    Returns:
        {
            "sweep_up": bool,
            "sweep_down": bool,
            "hit_liquidity_above": bool,
            "hit_liquidity_below": bool,
            "post_reversal": bool,
            "swept_prices": list
        }
    """
    if df is None or len(df) < lookback + 2:
        return {
            "sweep_up": False,
            "sweep_down": False,
            "hit_liquidity_above": False,
            "hit_liquidity_below": False,
            "post_reversal": False,
            "post_move": 0
        }

    # Анализируем последние 3 свечи для паттерна sweep
    # Sweep = резкое движение с возвратом (не одна свеча!)
    if len(df) < 3:
        return {
            "sweep_up": False,
            "sweep_down": False,
            "hit_liquidity_above": False,
            "hit_liquidity_below": False,
            "post_reversal": False,
            "post_move": 0,
            "swept_prices": []
        }
    
    last_3 = df.iloc[-3:]  # Последние 3 свечи
    highs = df["high"].iloc[-(lookback + 1):-3]  # Исключаем последние 3 свечи
    lows = df["low"].iloc[-(lookback + 1):-3]

    sweep_up = False
    sweep_down = False
    hit_above = False
    hit_below = False
    post_reversal = False
    post_move = 0
    
    # Максимум/минимум исторических данных (без последних 3 свечей)
    historical_high = highs.max() if len(highs) > 0 else last_3.iloc[0]["high"]
    historical_low = lows.min() if len(lows) > 0 else last_3.iloc[0]["low"]

    # SWEEP ВВЕРХ (bull trap): паттерн из 2-3 свечей
    # 1. Одна или несколько свечей прокалывают исторический максимум
    # 2. Быстрый возврат вниз (close < исторический максимум)
    max_in_pattern = last_3["high"].max()
    last_close = last_3.iloc[-1]["close"]
    first_close = last_3.iloc[0]["close"]
    
    if max_in_pattern > historical_high and last_close < historical_high:
        # Проверяем что это был БЫСТРЫЙ возврат (не медленное падение)
        # Хотя бы одна свеча в последних 3 должна закрыться значительно ниже прокола
        significant_return = False
        for candle in last_3.itertuples():
            if candle.high > historical_high and candle.close < historical_high * 0.998:  # -0.2%
                significant_return = True
                break
        
        if significant_return:
            sweep_up = True
            post_move = historical_high - last_close

    # SWEEP ВНИЗ (bear trap): паттерн из 2-3 свечей
    # 1. Одна или несколько свечей прокалывают исторический минимум
    # 2. Быстрый возврат вверх (close > исторический минимум)
    min_in_pattern = last_3["low"].min()
    
    if min_in_pattern < historical_low and last_close > historical_low:
        # Проверяем что это был БЫСТРЫЙ возврат
        significant_return = False
        for candle in last_3.itertuples():
            if candle.low < historical_low and candle.close > historical_low * 1.002:  # +0.2%
                significant_return = True
                break
        
        if significant_return:
            sweep_down = True
            post_move = last_close - historical_low

    # Проверка, задел ли свип стоп-уровни (проверяем по всем 3 свечам)
    if stop_prices_above:
        for p in stop_prices_above:
            for candle in last_3.itertuples():
                if candle.high >= p >= candle.close:
                    hit_above = True
                    break
            if hit_above:
                break
    
    if stop_prices_below:
        for p in stop_prices_below:
            for candle in last_3.itertuples():
                if candle.low <= p <= candle.close:
                    hit_below = True
                    break
            if hit_below:
                break

    # Оценка пост-реакции: если было возвращение внутрь диапазона
    if sweep_up:
        # Проверяем что закрытие существенно ниже прокола
        if last_close < historical_high * 0.998:  # -0.2%
            post_reversal = True
    
    if sweep_down:
        # Проверяем что закрытие существенно выше прокола
        if last_close > historical_low * 1.002:  # +0.2%
            post_reversal = True

    # Определяем swept цены (какие уровни были задеты)
    swept_prices = []
    if sweep_up:
        swept_prices.append({
            "price": historical_high,
            "direction": "up",
            "hit_liquidity": hit_above
        })
    if sweep_down:
        swept_prices.append({
            "price": historical_low,
            "direction": "down",
            "hit_liquidity": hit_below
        })
    
    return {
        "sweep_up": sweep_up,
        "sweep_down": sweep_down,
        "hit_liquidity_above": hit_above,
        "hit_liquidity_below": hit_below,
        "post_reversal": post_reversal,
        "post_move": post_move,
        "swept_prices": swept_prices  # Список swept уровней для инвалидации
    }


def detect_breakout(df, liquidity_level, direction="both", lookback=3):
    """
    Обнаруживает breakout (пробой с консолидацией) vs sweep (быстрый прокол с возвратом)
    
    Breakout = 2-3 свечи подряд закрываются выше/ниже уровня (медленное движение)
    Sweep = быстрый прокол и возврат (см. detect_sweep)
    
    Args:
        df: OHLCV DataFrame
        liquidity_level: уровень ликвидности для проверки
        direction: "up" (breakout вверх), "down" (breakout вниз), "both" (оба направления)
        lookback: сколько свечей должны закрыться выше/ниже уровня (default: 3)
    
    Returns:
        {
            "breakout_up": bool,
            "breakout_down": bool,
            "consolidation_candles": int,  # Сколько свечей подряд выше/ниже уровня
            "strong_breakout": bool,  # Все lookback свечей выше/ниже уровня
            "weak_breakout": bool,  # Только часть свечей выше/ниже
            "average_distance_pct": float  # Средняя дистанция от уровня в %
        }
    """
    if df is None or len(df) < lookback:
        return {
            "breakout_up": False,
            "breakout_down": False,
            "consolidation_candles": 0,
            "strong_breakout": False,
            "weak_breakout": False,
            "average_distance_pct": 0.0
        }
    
    last_candles = df.iloc[-lookback:]
    
    # Подсчитываем сколько свечей закрылись выше/ниже уровня
    candles_above = 0
    candles_below = 0
    distances_above = []
    distances_below = []
    
    for candle in last_candles.itertuples():
        if candle.close > liquidity_level:
            candles_above += 1
            distance_pct = ((candle.close - liquidity_level) / liquidity_level) * 100
            distances_above.append(distance_pct)
        elif candle.close < liquidity_level:
            candles_below += 1
            distance_pct = ((liquidity_level - candle.close) / liquidity_level) * 100
            distances_below.append(distance_pct)
    
    # BREAKOUT UP: большинство или все свечи закрылись выше уровня
    breakout_up = False
    strong_breakout_up = False
    weak_breakout_up = False
    avg_distance_up = 0.0
    
    if direction in ("up", "both"):
        if candles_above == lookback:
            # Все свечи выше = сильный breakout
            breakout_up = True
            strong_breakout_up = True
            avg_distance_up = sum(distances_above) / len(distances_above) if distances_above else 0.0
        elif candles_above >= lookback * 0.67:  # Минимум 2 из 3 свечей
            # Большинство свечей выше = слабый breakout
            breakout_up = True
            weak_breakout_up = True
            avg_distance_up = sum(distances_above) / len(distances_above) if distances_above else 0.0
    
    # BREAKOUT DOWN: большинство или все свечи закрылись ниже уровня
    breakout_down = False
    strong_breakout_down = False
    weak_breakout_down = False
    avg_distance_down = 0.0
    
    if direction in ("down", "both"):
        if candles_below == lookback:
            # Все свечи ниже = сильный breakout
            breakout_down = True
            strong_breakout_down = True
            avg_distance_down = sum(distances_below) / len(distances_below) if distances_below else 0.0
        elif candles_below >= lookback * 0.67:  # Минимум 2 из 3 свечей
            # Большинство свечей ниже = слабый breakout
            breakout_down = True
            weak_breakout_down = True
            avg_distance_down = sum(distances_below) / len(distances_below) if distances_below else 0.0
    
    return {
        "breakout_up": breakout_up,
        "breakout_down": breakout_down,
        "consolidation_candles": candles_above if breakout_up else candles_below,
        "strong_breakout": strong_breakout_up or strong_breakout_down,
        "weak_breakout": weak_breakout_up or weak_breakout_down,
        "average_distance_pct": avg_distance_up if breakout_up else avg_distance_down
    }


def detect_historical_sweeps(df, swing_highs, swing_lows, current_price, lookback_candles=100):
    """
    Обнаружение исторических sweeps swing levels:
    - Swing level был пробит ценой
    - Цена вернулась обратно (reversal)
    - Цена не возвращалась к этому уровню длительное время
    
    Args:
        df: OHLCV DataFrame
        swing_highs: список swing highs [{price, index}]
        swing_lows: список swing lows [{price, index}]
        current_price: текущая цена
        lookback_candles: сколько свечей анализировать (default: 100)
    
    Returns:
        list of swept swing levels [{price, direction, swept_at_index, recovery_confirmed}]
    """
    historical_sweeps = []
    
    if df is None or len(df) < 10:
        return historical_sweeps
    
    # Ограничиваем анализ последними N свечами
    start_idx = max(0, len(df) - lookback_candles)
    df_slice = df.iloc[start_idx:]
    
    # Анализируем swing lows (проверяем sweep вниз)
    for swing in swing_lows:
        swing_price = swing.get("price")
        swing_idx = swing.get("index", 0)
        
        if swing_price is None or swing_price >= current_price:
            continue  # Интересуют только уровни ниже текущей цены
        
        # Ищем свечи после swing, которые пробили его вниз
        swept = False
        swept_idx = None
        recovery_confirmed = False
        
        for i in range(swing_idx + 1, len(df)):
            candle = df.iloc[i]
            
            # Пробой вниз: low пробил swing_price
            if candle["low"] < swing_price and not swept:
                swept = True
                swept_idx = i
            
            # Восстановление: close вернулся выше swing_price
            if swept and candle["close"] > swing_price * 1.002:  # +0.2% подтверждение
                recovery_confirmed = True
                
                # Проверяем, не возвращались ли к этому уровню после
                no_retest = True
                for j in range(i + 5, len(df)):  # Минимум 5 свечей без ретеста
                    if abs(df.iloc[j]["close"] - swing_price) / swing_price < 0.005:  # < 0.5%
                        no_retest = False
                        break
                
                if no_retest:
                    historical_sweeps.append({
                        "price": swing_price,
                        "direction": "down",
                        "swept_at_index": swept_idx,
                        "recovery_confirmed": True,
                        "type": "swing_low",
                        "candles_ago": len(df) - swept_idx
                    })
                break
    
    # Анализируем swing highs (проверяем sweep вверх)
    for swing in swing_highs:
        swing_price = swing.get("price")
        swing_idx = swing.get("index", 0)
        
        if swing_price is None or swing_price <= current_price:
            continue  # Интересуют только уровни выше текущей цены
        
        # Ищем свечи после swing, которые пробили его вверх
        swept = False
        swept_idx = None
        recovery_confirmed = False
        
        for i in range(swing_idx + 1, len(df)):
            candle = df.iloc[i]
            
            # Пробой вверх: high пробил swing_price
            if candle["high"] > swing_price and not swept:
                swept = True
                swept_idx = i
            
            # Восстановление: close вернулся ниже swing_price
            if swept and candle["close"] < swing_price * 0.998:  # -0.2% подтверждение
                recovery_confirmed = True
                
                # Проверяем, не возвращались ли к этому уровню после
                no_retest = True
                for j in range(i + 5, len(df)):  # Минимум 5 свечей без ретеста
                    if abs(df.iloc[j]["close"] - swing_price) / swing_price < 0.005:  # < 0.5%
                        no_retest = False
                        break
                
                if no_retest:
                    historical_sweeps.append({
                        "price": swing_price,
                        "direction": "up",
                        "swept_at_index": swept_idx,
                        "recovery_confirmed": True,
                        "type": "swing_high",
                        "candles_ago": len(df) - swept_idx
                    })
                break
    
    return historical_sweeps

