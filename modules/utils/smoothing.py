# modules/utils/smoothing.py

import pandas as pd


def smooth_data(series, window=5):
    """
    Сглаживание данных методом скользящего среднего
    
    Args:
        series: pandas Series
        window: размер окна
        
    Returns:
        Сглаженный Series
    """
    return series.rolling(window=window).mean()


def exponential_smooth(series, alpha=0.3):
    """
    Экспоненциальное сглаживание
    
    Args:
        series: pandas Series
        alpha: коэффициент сглаживания (0-1)
        
    Returns:
        Сглаженный Series
    """
    return series.ewm(alpha=alpha, adjust=False).mean()

