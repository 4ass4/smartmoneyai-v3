# modules/ta_engine/atr.py

import pandas as pd


def calculate_atr(df, period=14):
    """
    Расчёт Average True Range (ATR) — мера волатильности
    
    Args:
        df: DataFrame с OHLCV
        period: период для усреднения
        
    Returns:
        Series с ATR значениями
    """
    if df.empty or len(df) < period + 1:
        return pd.Series([0] * len(df), index=df.index)
    
    # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # ATR = EMA of TR
    atr = true_range.ewm(span=period, adjust=False).mean()
    
    return atr


def calculate_atr_pct(df, period=14):
    """
    ATR в процентах от цены (нормированный ATR)
    
    Args:
        df: DataFrame с OHLCV
        period: период для усреднения
        
    Returns:
        Series с ATR% значениями
    """
    atr = calculate_atr(df, period)
    atr_pct = (atr / df['close']) * 100
    return atr_pct

