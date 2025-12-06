# modules/svd/cvd.py

"""
CVD (Cumulative Volume Delta) - накопительная дельта объёмов
Критичный индикатор для определения истинного направления money flow
"""

import pandas as pd


class CVDCalculator:
    """
    Рассчитывает CVD (Cumulative Volume Delta) с различными режимами reset
    """
    
    def __init__(self):
        self.cvd_value = 0.0
        self.history = []
        self.last_reset_price = None
    
    def calculate_cvd_from_trades(self, trades, reset_on_swing=False, swing_points=None):
        """
        Рассчитывает CVD из списка сделок
        
        Args:
            trades: list of dict с полями {side, volume, price, timestamp}
            reset_on_swing: сбрасывать ли CVD на swing points
            swing_points: dict с highs/lows для reset
            
        Returns:
            dict: {
                "cvd": float - текущее значение,
                "cvd_change": float - изменение за период,
                "cvd_slope": float - наклон (trend),
                "divergence": bool - есть ли дивергенция с ценой
            }
        """
        if not trades or len(trades) < 2:
            return {
                "cvd": self.cvd_value,
                "cvd_change": 0.0,
                "cvd_slope": 0.0,
                "divergence": False
            }
        
        # Сохраняем начальное значение для расчёта изменения
        initial_cvd = self.cvd_value
        
        # Проверяем reset на swing
        if reset_on_swing and swing_points:
            last_price = trades[-1].get("price")
            if self._should_reset_cvd(last_price, swing_points):
                self.cvd_value = 0.0
                self.last_reset_price = last_price
        
        # Накапливаем дельту
        for trade in trades:
            if not isinstance(trade, dict):
                continue
            
            side = trade.get("side", "").lower()
            volume = float(trade.get("volume", 0))
            
            if side == "buy":
                self.cvd_value += volume
            elif side == "sell":
                self.cvd_value -= volume
        
        # Рассчитываем изменение
        cvd_change = self.cvd_value - initial_cvd
        
        # Сохраняем в историю (ограничиваем размер)
        self.history.append(self.cvd_value)
        if len(self.history) > 100:
            self.history.pop(0)
        
        # Рассчитываем наклон (trend) - линейная регрессия по последним N точкам
        cvd_slope = self._calculate_slope(self.history[-20:] if len(self.history) >= 20 else self.history)
        
        # Детектируем дивергенцию (если цена растёт, а CVD падает или наоборот)
        divergence = self._detect_divergence(trades)
        
        return {
            "cvd": self.cvd_value,
            "cvd_change": cvd_change,
            "cvd_slope": cvd_slope,
            "divergence": divergence,
            "cvd_history_size": len(self.history)
        }
    
    def _should_reset_cvd(self, current_price, swing_points):
        """
        Определяет, нужно ли сбросить CVD на swing point
        """
        if not self.last_reset_price:
            return False
        
        highs = swing_points.get("highs", [])
        lows = swing_points.get("lows", [])
        
        # Проверяем, пробили ли мы новый swing high или low
        if highs and current_price > highs[-1].get("price", 0):
            return True
        if lows and current_price < lows[-1].get("price", float('inf')):
            return True
        
        return False
    
    def _calculate_slope(self, values):
        """
        Рассчитывает наклон (slope) через простую линейную регрессию
        
        Returns:
            float: положительный = uptrend, отрицательный = downtrend
        """
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x = list(range(n))
        y = values
        
        # Линейная регрессия: y = mx + b
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope
    
    def _detect_divergence(self, trades):
        """
        Детектирует дивергенцию между CVD и ценой
        
        Returns:
            bool: True если есть дивергенция
        """
        if len(self.history) < 20 or len(trades) < 10:
            return False
        
        # Берём последние 20 точек CVD
        recent_cvd = self.history[-20:]
        
        # Берём последние 10 сделок для определения тренда цены
        recent_prices = [float(t.get("price", 0)) for t in trades[-10:] if isinstance(t, dict)]
        
        if len(recent_prices) < 5:
            return False
        
        # Тренд цены (первая половина vs вторая половина)
        mid = len(recent_prices) // 2
        price_first_half = sum(recent_prices[:mid]) / mid
        price_second_half = sum(recent_prices[mid:]) / (len(recent_prices) - mid)
        price_trend_up = price_second_half > price_first_half
        
        # Тренд CVD
        cvd_mid = len(recent_cvd) // 2
        cvd_first_half = sum(recent_cvd[:cvd_mid]) / cvd_mid
        cvd_second_half = sum(recent_cvd[cvd_mid:]) / (len(recent_cvd) - cvd_mid)
        cvd_trend_up = cvd_second_half > cvd_first_half
        
        # Дивергенция = тренды в разных направлениях
        divergence = (price_trend_up != cvd_trend_up)
        
        return divergence
    
    def reset(self):
        """Сбрасывает CVD в 0"""
        self.cvd_value = 0.0
        self.last_reset_price = None


def calculate_cvd_from_df(df):
    """
    Рассчитывает CVD из DataFrame со свечами (упрощённая версия)
    
    Args:
        df: DataFrame с колонками [close, volume]
        
    Returns:
        Series: CVD значения
    """
    if df.empty or 'close' not in df.columns or 'volume' not in df.columns:
        return pd.Series([0] * len(df))
    
    # Упрощённое приближение: если close > prev_close → buy, иначе sell
    price_change = df['close'].diff()
    
    delta = df['volume'].copy()
    delta[price_change < 0] = -delta[price_change < 0]
    
    cvd = delta.cumsum()
    
    return cvd

