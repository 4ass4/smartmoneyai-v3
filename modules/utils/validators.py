# modules/utils/validators.py


def validate_ohlcv(df):
    """
    Валидация OHLCV данных
    
    Args:
        df: DataFrame с OHLCV данными
        
    Returns:
        Tuple (is_valid, errors)
    """
    errors = []
    
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Отсутствует колонка: {col}")
    
    if errors:
        return False, errors
    
    # Проверка логики OHLC
    if len(df) > 0:
        if (df['high'] < df['low']).any():
            errors.append("High не может быть меньше Low")
        if (df['high'] < df['open']).any():
            errors.append("High не может быть меньше Open")
        if (df['high'] < df['close']).any():
            errors.append("High не может быть меньше Close")
        if (df['low'] > df['open']).any():
            errors.append("Low не может быть больше Open")
        if (df['low'] > df['close']).any():
            errors.append("Low не может быть больше Close")
    
    return len(errors) == 0, errors


def validate_price(price):
    """Валидация цены"""
    if price is None:
        return False, "Цена не может быть None"
    if price <= 0:
        return False, "Цена должна быть положительной"
    return True, None

