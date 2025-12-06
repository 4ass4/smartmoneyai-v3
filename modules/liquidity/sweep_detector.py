def detect_sweep(df, lookback: int = 5, stop_prices_above=None, stop_prices_below=None):
    """
    Обнаружение ликвидити-свипа на последних свечах:
      - sweep_up: прокол недавних хайев с возвратом
      - sweep_down: прокол недавних лоев с возвратом

    Args:
        df: OHLCV DataFrame
        lookback: сколько предыдущих свечей брать для хай/лоу

    Дополнительно можно передать уровни стопов/ликвидности:
        stop_prices_above: список цен стопов выше (buy stops)
        stop_prices_below: список цен стопов ниже (sell stops)

    Returns:
        {
            "sweep_up": bool,
            "sweep_down": bool,
            "hit_liquidity_above": bool,
            "hit_liquidity_below": bool
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

