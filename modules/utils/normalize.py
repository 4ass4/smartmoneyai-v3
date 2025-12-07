# modules/utils/normalize.py

"""
Нормализация метрик на волатильность (ATR) для учета рыночных условий
"""


def normalize_delta_on_atr(delta, atr_pct, base_threshold=0.5):
    """
    Нормирует дельту на ATR для учёта волатильности
    
    Args:
        delta: абсолютная дельта объёмов
        atr_pct: ATR в процентах от цены
        base_threshold: базовый порог для нормальной волатильности (0.5%)
        
    Returns:
        normalized_delta: нормированная дельта
    """
    if atr_pct == 0:
        return delta
    
    # Коэффициент нормировки: при высокой волатильности дельта менее значима
    norm_factor = base_threshold / max(atr_pct, 0.1)
    normalized = delta * norm_factor
    
    return normalized


def normalize_price_move_on_atr(price_move_pct, atr_pct):
    """
    Нормирует движение цены на ATR
    
    Args:
        price_move_pct: движение цены в процентах
        atr_pct: ATR в процентах
        
    Returns:
        normalized_move: нормированное движение (в единицах ATR)
    """
    if atr_pct == 0:
        return price_move_pct
    
    # Движение в единицах ATR
    return price_move_pct / atr_pct


def get_absorption_threshold(atr_pct, base_threshold=0.05):
    """
    Адаптивный порог для absorption detection на основе ATR
    
    Args:
        atr_pct: ATR в процентах
        base_threshold: базовый порог для нормальной волатильности (0.05%)
        
    Returns:
        threshold: адаптивный порог
    """
    # При высокой волатильности порог выше
    return base_threshold + (atr_pct / 10)


def normalize_path_cost_on_atr(path_cost_up, path_cost_down, atr_pct):
    """
    Нормирует path cost на ATR для сравнимости при разной волатильности
    
    Args:
        path_cost_up: стоимость пути вверх
        path_cost_down: стоимость пути вниз
        atr_pct: ATR в процентах
        
    Returns:
        dict: {"up": normalized_up, "down": normalized_down}
    """
    if atr_pct == 0:
        return {"up": path_cost_up, "down": path_cost_down}
    
    # Нормируем на ATR: при высокой волатильности стакан "шире", cost растёт
    norm_factor = 1.0 / max(atr_pct, 0.1)
    
    return {
        "up": path_cost_up * norm_factor,
        "down": path_cost_down * norm_factor
    }


def get_sweep_threshold(atr_pct, base_threshold=0.15):
    """
    Адаптивный порог для sweep detection (в % от ATR)
    
    Args:
        atr_pct: ATR в процентах
        base_threshold: базовый порог относительно ATR
        
    Returns:
        threshold: порог в процентах цены
    """
    # Свип должен быть минимум base_threshold * ATR
    return atr_pct * base_threshold




