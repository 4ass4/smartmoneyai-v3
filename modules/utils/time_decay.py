# modules/utils/time_decay.py

"""
Time-decay функции для снижения веса старых уровней
"""

import time


def calculate_time_decay(timestamp, current_timestamp=None, half_life_seconds=86400):
    """
    Вычисляет коэффициент time-decay (экспоненциальный)
    
    Args:
        timestamp: timestamp уровня (ms)
        current_timestamp: текущий timestamp (ms), если None - берём time.time()
        half_life_seconds: период полураспада в секундах (по умолчанию 24ч)
        
    Returns:
        float: коэффициент от 0 до 1, где 1 = свежий, 0 = очень старый
    """
    if current_timestamp is None:
        current_timestamp = int(time.time() * 1000)
    
    if timestamp is None or timestamp <= 0:
        # Если нет timestamp - считаем старым
        return 0.5
    
    age_ms = current_timestamp - timestamp
    age_seconds = age_ms / 1000
    
    if age_seconds < 0:
        # Уровень "из будущего" - вероятно ошибка, но даём полный вес
        return 1.0
    
    # Экспоненциальный decay: weight = 0.5^(age / half_life)
    import math
    decay = math.pow(0.5, age_seconds / half_life_seconds)
    
    return max(0.0, min(1.0, decay))


def apply_decay_to_levels(levels, current_timestamp=None, half_life_seconds=86400):
    """
    Применяет time-decay к списку уровней
    
    Args:
        levels: list of dict с полями {"price":..., "timestamp":..., ...}
        current_timestamp: текущий timestamp (ms)
        half_life_seconds: период полураспада
        
    Returns:
        list: тот же список, но с добавленным полем "decay_weight"
    """
    if current_timestamp is None:
        current_timestamp = int(time.time() * 1000)
    
    for level in levels:
        level_ts = level.get("timestamp")
        decay_weight = calculate_time_decay(level_ts, current_timestamp, half_life_seconds)
        level["decay_weight"] = decay_weight
    
    return levels


def get_weighted_importance(base_importance, decay_weight):
    """
    Возвращает взвешенную важность уровня с учётом time-decay
    
    Args:
        base_importance: базовая важность (например, объём, сила уровня)
        decay_weight: коэффициент time-decay (0-1)
        
    Returns:
        float: взвешенная важность
    """
    return base_importance * decay_weight

