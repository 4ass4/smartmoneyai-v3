# modules/liquidity/stop_clusters.py

# Минимальный анализ объёмов + ценовых областей.

import numpy as np


def detect_stop_clusters(df):
    """
    Находим зоны, где вероятно стоят стопы толпы:
    - над локальными high
    - под локальными low
    - аномальные тени (wicks)
    """

    clusters = []

    for i in range(2, len(df)):
        high = df['high'][i]
        low = df['low'][i]

        # Длинная верхняя тень → стопы покупателей выше high
        upper_wick = df['high'][i] - max(df['open'][i], df['close'][i])
        if upper_wick > (df['high'][i] - df['low'][i]) * 0.6:
            clusters.append({"type": "buy_stops", "price": high, "source": "wick"})

        # Длинная нижняя тень → стопы продавцов под low
        lower_wick = min(df['open'][i], df['close'][i]) - df['low'][i]
        if lower_wick > (df['high'][i] - df['low'][i]) * 0.6:
            clusters.append({"type": "sell_stops", "price": low, "source": "wick"})

    return clusters

