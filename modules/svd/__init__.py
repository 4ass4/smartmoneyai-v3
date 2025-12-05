"""
SVD Engine v1.0 (Smart Volume Dynamics)
Анализ потока ордеров, поглощений, агрессии и намерений крупных игроков
"""

from .svd_engine import SVDEngine
from .delta import compute_delta
from .absorption import detect_absorption
from .aggression import detect_aggression
from .velocity import detect_trade_velocity
from .svd_score import svd_confidence_score

__all__ = [
    'SVDEngine',
    'compute_delta',
    'detect_absorption',
    'detect_aggression',
    'detect_trade_velocity',
    'svd_confidence_score'
]

