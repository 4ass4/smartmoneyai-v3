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

    last = df.iloc[-1]
    prev = df.iloc[-2]
    highs = df["high"].iloc[-(lookback + 1):-1]
    lows = df["low"].iloc[-(lookback + 1):-1]

    sweep_up = False
    sweep_down = False
    hit_above = False
    hit_below = False
    post_reversal = False
    post_move = 0

    # Sweep вверх: текущий хай > max предыдущих, но закрытие ниже max предыдущих
    if last["high"] > highs.max() and last["close"] < highs.max():
        sweep_up = True

    # Sweep вниз: текущий лоу < min предыдущих, но закрытие выше min предыдущих
    if last["low"] < lows.min() and last["close"] > lows.min():
        sweep_down = True

    # Проверка, задел ли свип стоп-уровни
    if stop_prices_above:
        for p in stop_prices_above:
            if last["high"] >= p >= last["close"]:
                hit_above = True
                break
    if stop_prices_below:
        for p in stop_prices_below:
            if last["low"] <= p <= last["close"]:
                hit_below = True
                break

    # Оценка пост-реакции: если было возвращение внутрь диапазона и движение против пробоя
    if sweep_up:
        post_move = highs.max() - last["close"]
        # пост-реверсал, если закрылись существенно ниже прокола
        if last["close"] < highs.max() * 0.999:
            post_reversal = True
    if sweep_down:
        post_move = last["close"] - lows.min()
        if last["close"] > lows.min() * 1.001:
            post_reversal = True

    # Определяем swept цены (какие уровни были задеты)
    swept_prices = []
    if sweep_up:
        swept_prices.append({
            "price": highs.max(),
            "direction": "up",
            "hit_liquidity": hit_above
        })
    if sweep_down:
        swept_prices.append({
            "price": lows.min(),
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

