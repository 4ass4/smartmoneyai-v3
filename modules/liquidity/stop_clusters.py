# modules/liquidity/stop_clusters.py

# Минимальный анализ объёмов + ценовых областей.

import numpy as np
from modules.utils.time_decay import calculate_time_decay
import time


def detect_stop_clusters(df, apply_time_decay=True):
    """
    Находим зоны, где вероятно стоят стопы толпы:
    - над локальными high
    - под локальными low
    - аномальные тени (wicks)
    
    Args:
        df: DataFrame с OHLCV и timestamp
        apply_time_decay: применять ли time-decay к старым кластерам
    """

    clusters = []
    current_ts = int(time.time() * 1000)

    for i in range(2, len(df)):
        high = df['high'].iloc[i]
        low = df['low'].iloc[i]
        
        # Получаем timestamp свечи
        candle_ts = df['timestamp'].iloc[i] if 'timestamp' in df.columns else current_ts

        # Длинная верхняя тень → стопы покупателей выше high
        upper_wick = df['high'].iloc[i] - max(df['open'].iloc[i], df['close'].iloc[i])
        if upper_wick > (df['high'].iloc[i] - df['low'].iloc[i]) * 0.6:
            decay_weight = calculate_time_decay(candle_ts, current_ts) if apply_time_decay else 1.0
            clusters.append({
                "type": "buy_stops",
                "price": high,
                "source": "wick",
                "timestamp": candle_ts,
                "decay_weight": decay_weight
            })

        # Длинная нижняя тень → стопы продавцов под low
        lower_wick = min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]
        if lower_wick > (df['high'].iloc[i] - df['low'].iloc[i]) * 0.6:
            decay_weight = calculate_time_decay(candle_ts, current_ts) if apply_time_decay else 1.0
            clusters.append({
                "type": "sell_stops",
                "price": low,
                "source": "wick",
                "timestamp": candle_ts,
                "decay_weight": decay_weight
            })

    return clusters

