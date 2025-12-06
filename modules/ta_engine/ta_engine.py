# modules/ta_engine/ta_engine.py

from .ema import calculate_ema
from .rsi import calculate_rsi
from .patterns import detect_patterns
from .atr import calculate_atr, calculate_atr_pct


class TAEngine:
    """
    Минималистичный TA Engine v3
    Только самое необходимое для Smart Money анализа
    """

    def __init__(self):
        pass

    def analyze(self, df):
        """
        Основной метод технического анализа
        
        Args:
            df: DataFrame с OHLCV данными
            
        Returns:
            Dict с результатами TA анализа
        """
        # EMA
        ema_fast = calculate_ema(df, period=20)
        ema_slow = calculate_ema(df, period=50)
        
        # RSI
        rsi = calculate_rsi(df, period=14)
        
        # ATR (волатильность)
        atr = calculate_atr(df, period=14)
        atr_pct = calculate_atr_pct(df, period=14)
        
        # Паттерны
        patterns = detect_patterns(df)
        
        # Определение тренда по EMA
        current_price = df['close'].iloc[-1]
        trend = "neutral"
        
        if ema_fast.iloc[-1] > ema_slow.iloc[-1] and current_price > ema_fast.iloc[-1]:
            trend = "bullish"
        elif ema_fast.iloc[-1] < ema_slow.iloc[-1] and current_price < ema_fast.iloc[-1]:
            trend = "bearish"
        
        return {
            "ema_fast": ema_fast.iloc[-1],
            "ema_slow": ema_slow.iloc[-1],
            "rsi": rsi.iloc[-1],
            "trend": trend,
            "patterns": patterns,
            "overbought": rsi.iloc[-1] > 70,
            "oversold": rsi.iloc[-1] < 30,
            "atr": atr.iloc[-1],
            "atr_pct": atr_pct.iloc[-1]  # В процентах от цены
        }

