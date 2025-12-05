def detect_sweep(df, lookback: int = 5):
    """
    Обнаружение ликвидити-свипа на последних свечах:
      - sweep_up: прокол недавних хайев с возвратом
      - sweep_down: прокол недавних лоев с возвратом

    Args:
        df: OHLCV DataFrame
        lookback: сколько предыдущих свечей брать для хай/лоу

    Returns:
        {"sweep_up": bool, "sweep_down": bool}
    """
    if df is None or len(df) < lookback + 2:
        return {"sweep_up": False, "sweep_down": False}

    last = df.iloc[-1]
    prev = df.iloc[-2]
    highs = df["high"].iloc[-(lookback + 1):-1]
    lows = df["low"].iloc[-(lookback + 1):-1]

    sweep_up = False
    sweep_down = False

    # Sweep вверх: текущий хай > max предыдущих, но закрытие ниже max предыдущих
    if last["high"] > highs.max() and last["close"] < highs.max():
        sweep_up = True

    # Sweep вниз: текущий лоу < min предыдущих, но закрытие выше min предыдущих
    if last["low"] < lows.min() and last["close"] > lows.min():
        sweep_down = True

    return {"sweep_up": sweep_up, "sweep_down": sweep_down}

