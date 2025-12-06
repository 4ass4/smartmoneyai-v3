def detect_swings(df, lookback=2, volume_threshold=1.2):
    """
    Находим swing highs и swing lows с расширенным контекстом.
    
    Args:
        df: DataFrame с OHLCV
        lookback: количество свечей слева и справа для проверки (по умолчанию 2)
        volume_threshold: минимальный множитель объёма для "значимого" свинга
    
    Свинг = экстремум, окружённый lookback свечами с обеих сторон.
    Дополнительная оценка значимости: объём, размах, расстояние до других свингов.
    """

    highs = []
    lows = []
    
    if len(df) < lookback * 2 + 1:
        return {"highs": highs, "lows": lows}
    
    # Средний объём для оценки значимости
    avg_volume = df['volume'].mean() if 'volume' in df.columns else 0

    for i in range(lookback, len(df) - lookback):
        # Swing High: цена выше всех соседних свечей
        is_swing_high = True
        for offset in range(1, lookback + 1):
            if df['high'].iloc[i] <= df['high'].iloc[i - offset] or \
               df['high'].iloc[i] <= df['high'].iloc[i + offset]:
                is_swing_high = False
                break
        
        if is_swing_high:
            # Оцениваем значимость свинга
            swing_volume = df['volume'].iloc[i] if 'volume' in df.columns else avg_volume
            volume_significance = swing_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Размах свечи (волатильность на момент свинга)
            candle_range = df['high'].iloc[i] - df['low'].iloc[i]
            avg_range = (df['high'] - df['low']).mean()
            range_significance = candle_range / avg_range if avg_range > 0 else 1.0
            
            # Общая значимость
            significance = (volume_significance + range_significance) / 2
            
            swing_data = {
                "index": i,
                "price": df['high'].iloc[i],
                "significance": significance,
                "volume": swing_volume,
                "candle_range": candle_range
            }
            # Добавляем timestamp если есть
            if 'timestamp' in df.columns:
                swing_data["timestamp"] = df['timestamp'].iloc[i]
            
            # Фильтр: только значимые свинги (объём выше threshold или большой range)
            if volume_significance >= volume_threshold or range_significance >= 1.5:
                highs.append(swing_data)
        
        # Swing Low: цена ниже всех соседних свечей
        is_swing_low = True
        for offset in range(1, lookback + 1):
            if df['low'].iloc[i] >= df['low'].iloc[i - offset] or \
               df['low'].iloc[i] >= df['low'].iloc[i + offset]:
                is_swing_low = False
                break
        
        if is_swing_low:
            # Оцениваем значимость свинга
            swing_volume = df['volume'].iloc[i] if 'volume' in df.columns else avg_volume
            volume_significance = swing_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Размах свечи
            candle_range = df['high'].iloc[i] - df['low'].iloc[i]
            avg_range = (df['high'] - df['low']).mean()
            range_significance = candle_range / avg_range if avg_range > 0 else 1.0
            
            # Общая значимость
            significance = (volume_significance + range_significance) / 2
            
            swing_data = {
                "index": i,
                "price": df['low'].iloc[i],
                "significance": significance,
                "volume": swing_volume,
                "candle_range": candle_range
            }
            # Добавляем timestamp если есть
            if 'timestamp' in df.columns:
                swing_data["timestamp"] = df['timestamp'].iloc[i]
            
            # Фильтр: только значимые свинги
            if volume_significance >= volume_threshold or range_significance >= 1.5:
                lows.append(swing_data)

    return {"highs": highs, "lows": lows}

