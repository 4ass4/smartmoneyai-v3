# modules/ta_engine/rsi.py

import pandas as pd


def calculate_rsi(df, period=14):
    """
    Расчет индикатора RSI (Relative Strength Index)
    
    Args:
        df: DataFrame с колонкой 'close'
        period: период RSI (по умолчанию 14)
        
    Returns:
        Series с RSI значениями (0-100)
    """
    delta = df['close'].diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

