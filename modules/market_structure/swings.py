def detect_swings(df):
    """
    Находим swing highs и swing lows.
    Свинг = экстремум, окружённый с 2 сторон свечами выше/ниже.
    """

    highs = []
    lows = []

    for i in range(2, len(df)-2):
        # Swing High
        if df['high'].iloc[i] > df['high'].iloc[i-1] and df['high'].iloc[i] > df['high'].iloc[i+1]:
            swing_data = {
                "index": i,
                "price": df['high'].iloc[i]
            }
            # Добавляем timestamp если есть
            if 'timestamp' in df.columns:
                swing_data["timestamp"] = df['timestamp'].iloc[i]
            highs.append(swing_data)

        # Swing Low
        if df['low'].iloc[i] < df['low'].iloc[i-1] and df['low'].iloc[i] < df['low'].iloc[i+1]:
            swing_data = {
                "index": i,
                "price": df['low'].iloc[i]
            }
            # Добавляем timestamp если есть
            if 'timestamp' in df.columns:
                swing_data["timestamp"] = df['timestamp'].iloc[i]
            lows.append(swing_data)

    return {"highs": highs, "lows": lows}

