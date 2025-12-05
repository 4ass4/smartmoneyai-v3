# modules/ta_engine/patterns.py


def detect_patterns(df):
    """
    Минималистичное определение свечных паттернов
    
    Args:
        df: DataFrame с OHLCV данными
        
    Returns:
        List обнаруженных паттернов
    """
    patterns = []
    
    if len(df) < 3:
        return patterns
    
    # Последние 3 свечи
    c1 = df.iloc[-3]
    c2 = df.iloc[-2]
    c3 = df.iloc[-1]
    
    # Engulfing patterns
    # Bullish Engulfing
    if (c1['close'] < c1['open'] and  # первая медвежья
        c2['open'] < c1['close'] and   # открытие ниже закрытия первой
        c2['close'] > c1['open']):     # закрытие выше открытия первой
        patterns.append({"type": "bullish_engulfing", "strength": "medium"})
    
    # Bearish Engulfing
    if (c1['close'] > c1['open'] and  # первая бычья
        c2['open'] > c1['close'] and  # открытие выше закрытия первой
        c2['close'] < c1['open']):    # закрытие ниже открытия первой
        patterns.append({"type": "bearish_engulfing", "strength": "medium"})
    
    # Hammer / Doji (упрощенно)
    body = abs(c3['close'] - c3['open'])
    total_range = c3['high'] - c3['low']
    
    if total_range > 0:
        body_ratio = body / total_range
        
        # Hammer (маленькое тело, длинная нижняя тень)
        lower_wick = min(c3['open'], c3['close']) - c3['low']
        if body_ratio < 0.3 and lower_wick > total_range * 0.6:
            patterns.append({"type": "hammer", "strength": "medium"})
        
        # Doji (очень маленькое тело)
        if body_ratio < 0.1:
            patterns.append({"type": "doji", "strength": "low"})
    
    return patterns

