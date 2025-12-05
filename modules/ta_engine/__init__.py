"""
TA Engine v3 - Минималистичный технический анализ
"""

from .ta_engine import TAEngine
from .ema import calculate_ema
from .rsi import calculate_rsi
from .patterns import detect_patterns

__all__ = [
    'TAEngine',
    'calculate_ema',
    'calculate_rsi',
    'detect_patterns'
]

