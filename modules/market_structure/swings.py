def detect_swings(df):
    """
    Находим swing highs и swing lows.
    Свинг = экстремум, окружённый с 2 сторон свечами выше/ниже.
    """

    highs = []
    lows = []

    for i in range(2, len(df)-2):
        # Swing High
        if df['high'][i] > df['high'][i-1] and df['high'][i] > df['high'][i+1]:
            highs.append({"index": i, "price": df['high'][i]})

        # Swing Low
        if df['low'][i] < df['low'][i-1] and df['low'][i] < df['low'][i+1]:
            lows.append({"index": i, "price": df['low'][i]})

    return {"highs": highs, "lows": lows}

