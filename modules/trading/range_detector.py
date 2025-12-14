# modules/trading/range_detector.py

"""
Детектор боковых коридоров (range) для торговли в фазах накопления
Определяет границы коридора и точки входа
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class RangeDetector:
    """
    Определяет боковые коридоры (range) для торговли
    """
    
    def __init__(self, lookback_candles=20, range_threshold_pct=2.0):
        """
        Args:
            lookback_candles: количество свечей для анализа коридора
            range_threshold_pct: порог в % для определения боковика (если диапазон < threshold → range)
        """
        self.lookback_candles = lookback_candles
        self.range_threshold_pct = range_threshold_pct
    
    def detect_range(self, df, current_price):
        """
        Определяет боковой коридор и его границы
        
        Args:
            df: OHLCV DataFrame
            current_price: текущая цена
        
        Returns:
            dict: {
                "is_range": bool,
                "range_high": float,  # Верхняя граница коридора
                "range_low": float,    # Нижняя граница коридора
                "range_width_pct": float,  # Ширина коридора в %
                "current_position": "top" | "middle" | "bottom",  # Позиция цены в коридоре
                "distance_to_low_pct": float,  # Расстояние до нижней границы в %
                "distance_to_high_pct": float,  # Расстояние до верхней границы в %
                "range_quality": 0.0-1.0  # Качество коридора (насколько чёткий)
            }
        """
        if df is None or len(df) < self.lookback_candles:
            return {
                "is_range": False,
                "range_high": current_price,
                "range_low": current_price,
                "range_width_pct": 0.0,
                "current_position": "middle",
                "distance_to_low_pct": 0.0,
                "distance_to_high_pct": 0.0,
                "range_quality": 0.0
            }
        
        # Анализируем последние N свечей
        recent = df.iloc[-self.lookback_candles:]
        
        # Определяем границы
        range_high = recent['high'].max()
        range_low = recent['low'].min()
        range_width = range_high - range_low
        range_width_pct = (range_width / range_low) * 100
        
        # Проверяем является ли это боковиком
        # Боковик: диапазон < threshold И цена не выходит за границы
        is_range = (
            range_width_pct < self.range_threshold_pct and
            current_price >= range_low * 0.99 and  # В пределах 1% от границ
            current_price <= range_high * 1.01
        )
        
        # Определяем позицию цены в коридоре
        if current_price >= range_high * 0.95:  # Верхние 5%
            current_position = "top"
        elif current_price <= range_low * 1.05:  # Нижние 5%
            current_position = "bottom"
        else:
            current_position = "middle"
        
        # Расстояния до границ
        distance_to_low_pct = ((current_price - range_low) / range_low) * 100
        distance_to_high_pct = ((range_high - current_price) / current_price) * 100
        
        # Качество коридора (насколько чёткий)
        # Проверяем сколько раз цена касалась границ
        touches_high = (recent['high'] >= range_high * 0.98).sum()
        touches_low = (recent['low'] <= range_low * 1.02).sum()
        range_quality = min(1.0, (touches_high + touches_low) / (self.lookback_candles * 0.3))
        
        result = {
            "is_range": is_range,
            "range_high": range_high,
            "range_low": range_low,
            "range_width_pct": range_width_pct,
            "current_position": current_position,
            "distance_to_low_pct": distance_to_low_pct,
            "distance_to_high_pct": distance_to_high_pct,
            "range_quality": range_quality
        }
        
        if is_range:
            logger.info(f"📊 Range detected: ${range_low:.2f} - ${range_high:.2f} "
                       f"(width: {range_width_pct:.2f}%, quality: {range_quality:.2f}, "
                       f"position: {current_position})")
        
        return result

