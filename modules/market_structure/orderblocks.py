def detect_orderblocks(swings, df):
    """
    Ультра-минимальная версия OB:
    - последний медвежий свечной блок перед импульсом вверх (bullish OB)
    - последний бычий блок перед импульсом вниз (bearish OB)
    """

    ob_list = []

    for i in range(3, len(df)-3):
        # Bullish Order Block (последняя медвежья перед ростом)
        if df['close'][i] < df['open'][i] and df['close'][i+1] > df['open'][i+1]:
            ob_list.append({
                "index": i,
                "type": "bullish",
                "low": df['low'][i],
                "high": df['high'][i]
            })

        # Bearish Order Block (последняя бычья перед падением)
        if df['close'][i] > df['open'][i] and df['close'][i+1] < df['open'][i+1]:
            ob_list.append({
                "index": i,
                "type": "bearish",
                "low": df['low'][i],
                "high": df['high'][i]
            })

    return ob_list

