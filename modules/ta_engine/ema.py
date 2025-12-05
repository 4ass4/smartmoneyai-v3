# modules/ta_engine/ema.py

import pandas as pd


def calculate_ema(df, period=20):
    """
    Расчет экспоненциальной скользящей средней
    
    Args:
        df: DataFrame с колонкой 'close'
        period: период EMA
        
    Returns:
        Series с EMA значениями
    """
    return df['close'].ewm(span=period, adjust=False).mean()

