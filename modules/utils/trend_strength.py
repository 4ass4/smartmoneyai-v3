# modules/utils/trend_strength.py

"""
Анализатор силы тренда
Определяет насколько сильный текущий тренд (momentum)
"""

import numpy as np
import pandas as pd


def calculate_trend_strength(df, lookback=20, multi_period=False):
    """
    Рассчитывает силу текущего тренда
    
    Args:
        df: OHLCV DataFrame
        lookback: период для анализа (default: 20)
        multi_period: если True, анализирует несколько периодов (20, 50, 100)
    
    Returns:
        dict: {
            "direction": "up"/"down"/"neutral",
            "strength": 0.0-1.0,  # 0 = нет тренда, 1 = очень сильный
            "momentum": float,  # скорость изменения цены
            "consistency": 0.0-1.0,  # насколько последовательный тренд
            "volume_confirmation": bool,  # подтверждается ли объёмом
            "multi_period": dict  # анализ на разных периодах (если multi_period=True)
        }
    """
    if df is None or len(df) < lookback:
        return {
            "direction": "neutral",
            "strength": 0.0,
            "momentum": 0.0,
            "consistency": 0.0,
            "volume_confirmation": False,
            "multi_period": {}
        }
    
    recent = df.iloc[-lookback:]
    
    # 1. Momentum (скорость изменения цены)
    first_close = recent["close"].iloc[0]
    last_close = recent["close"].iloc[-1]
    price_change_pct = ((last_close - first_close) / first_close) * 100
    
    # 2. Trend direction
    if price_change_pct > 1.0:
        direction = "up"
    elif price_change_pct < -1.0:
        direction = "down"
    else:
        direction = "neutral"
    
    # 3. Consistency (насколько последовательно движется цена)
    # Считаем сколько свечей движутся в направлении тренда
    closes = recent["close"].values
    price_diffs = np.diff(closes)
    
    if direction == "up":
        trend_candles = np.sum(price_diffs > 0)
    elif direction == "down":
        trend_candles = np.sum(price_diffs < 0)
    else:
        trend_candles = 0
    
    consistency = trend_candles / len(price_diffs) if len(price_diffs) > 0 else 0.0
    
    # 4. Volume confirmation
    # Проверяем растёт ли объём при движении в сторону тренда
    avg_volume = recent["volume"].mean()
    recent_volume = recent["volume"].iloc[-5:].mean()  # Последние 5 свечей
    
    volume_confirmation = recent_volume > avg_volume * 1.1  # +10% объём
    
    # 5. Strength (сила тренда)
    # Комбинация momentum, consistency и volume
    momentum_score = min(abs(price_change_pct) / 5.0, 1.0)  # 5% = max strength
    
    strength = (
        momentum_score * 0.5 +  # 50% - momentum
        consistency * 0.3 +     # 30% - consistency
        (0.2 if volume_confirmation else 0.0)  # 20% - volume
    )
    
    result = {
        "direction": direction,
        "strength": min(strength, 1.0),
        "momentum": price_change_pct,
        "consistency": consistency,
        "volume_confirmation": volume_confirmation,
        "multi_period": {}
    }
    
    # Если multi_period=True, добавляем анализ на разных периодах
    if multi_period:
        periods = {}
        for period in [20, 50, 100]:
            if len(df) >= period:
                period_result = _calculate_single_period(df, period)
                periods[f"{period}candles"] = period_result
        result["multi_period"] = periods
    
    return result


def _calculate_single_period(df, lookback):
    """Внутренняя функция для анализа на одном периоде"""
    recent = df.iloc[-lookback:]
    
    # 1. Momentum (скорость изменения цены)
    first_close = recent["close"].iloc[0]
    last_close = recent["close"].iloc[-1]
    price_change_pct = ((last_close - first_close) / first_close) * 100
    
    # 2. Trend direction
    if price_change_pct > 1.0:
        direction = "up"
    elif price_change_pct < -1.0:
        direction = "down"
    else:
        direction = "neutral"
    
    # 3. Consistency (насколько последовательно движется цена)
    closes = recent["close"].values
    price_diffs = np.diff(closes)
    
    if direction == "up":
        trend_candles = np.sum(price_diffs > 0)
    elif direction == "down":
        trend_candles = np.sum(price_diffs < 0)
    else:
        trend_candles = 0
    
    consistency = trend_candles / len(price_diffs) if len(price_diffs) > 0 else 0.0
    
    # 4. Volume confirmation
    avg_volume = recent["volume"].mean()
    recent_volume = recent["volume"].iloc[-5:].mean()  # Последние 5 свечей
    volume_confirmation = recent_volume > avg_volume * 1.1  # +10% объём
    
    # 5. Strength (сила тренда)
    momentum_score = min(abs(price_change_pct) / 5.0, 1.0)  # 5% = max strength
    strength = (
        momentum_score * 0.5 +  # 50% - momentum
        consistency * 0.3 +     # 30% - consistency
        (0.2 if volume_confirmation else 0.0)  # 20% - volume
    )
    
    return {
        "direction": direction,
        "strength": min(strength, 1.0),
        "momentum": price_change_pct,
        "consistency": consistency,
        "volume_confirmation": volume_confirmation
    }


def analyze_pullback_vs_reversal(df, trend_direction, lookback=50):
    """
    Определяет это pullback (коррекция) или reversal (разворот)
    
    Args:
        df: OHLCV DataFrame
        trend_direction: направление основного тренда ("up"/"down")
        lookback: период для анализа основного тренда
    
    Returns:
        dict: {
            "is_pullback": bool,  # True если это коррекция
            "is_reversal": bool,  # True если это разворот
            "pullback_depth_pct": float,  # глубина отката в %
            "confidence": 0.0-1.0  # уверенность в определении
        }
    """
    if df is None or len(df) < lookback:
        return {
            "is_pullback": False,
            "is_reversal": False,
            "pullback_depth_pct": 0.0,
            "confidence": 0.0
        }
    
    recent = df.iloc[-lookback:]
    last_20 = df.iloc[-20:]
    
    # Находим экстремумы основного тренда
    if trend_direction == "up":
        trend_high = recent["high"].max()
        current_price = last_20["close"].iloc[-1]
        pullback_depth_pct = ((trend_high - current_price) / trend_high) * 100
        
        # Pullback если откат < 20% от движения
        is_pullback = 0 < pullback_depth_pct < 20
        is_reversal = pullback_depth_pct > 30
        
    elif trend_direction == "down":
        trend_low = recent["low"].min()
        current_price = last_20["close"].iloc[-1]
        pullback_depth_pct = ((current_price - trend_low) / trend_low) * 100
        
        # Pullback если откат < 20% от движения
        is_pullback = 0 < pullback_depth_pct < 20
        is_reversal = pullback_depth_pct > 30
        
    else:
        return {
            "is_pullback": False,
            "is_reversal": False,
            "pullback_depth_pct": 0.0,
            "confidence": 0.0
        }
    
    # Confidence based on consistency
    # Если pullback быстрый и неглубокий → high confidence
    if is_pullback:
        confidence = 1.0 - (pullback_depth_pct / 20.0)  # Меньше откат = выше уверенность
    elif is_reversal:
        confidence = min(pullback_depth_pct / 30.0, 1.0)
    else:
        confidence = 0.5  # Neutral
    
    return {
        "is_pullback": is_pullback,
        "is_reversal": is_reversal,
        "pullback_depth_pct": pullback_depth_pct,
        "confidence": confidence
    }


def count_liquidity_targets(liquidity_data, current_price):
    """
    Подсчитывает цели ликвидности выше и ниже цены
    
    Args:
        liquidity_data: данные ликвидности
        current_price: текущая цена
    
    Returns:
        dict: {
            "targets_above": int,
            "targets_below": int,
            "primary_direction": "up"/"down"/"neutral",
            "nearest_above": float,
            "nearest_below": float
        }
    """
    stop_clusters = liquidity_data.get("stop_clusters", [])
    swing_liquidity = liquidity_data.get("swing_liquidity", [])
    
    targets_above = 0
    targets_below = 0
    nearest_above = None
    nearest_below = None
    
    # Подсчитываем stop_clusters
    for cluster in stop_clusters:
        price = cluster.get("price", 0)
        if price > current_price:
            targets_above += 1
            if nearest_above is None or price < nearest_above:
                nearest_above = price
        elif price < current_price:
            targets_below += 1
            if nearest_below is None or price > nearest_below:
                nearest_below = price
    
    # Подсчитываем swing_liquidity
    for swing in swing_liquidity:
        price = swing.get("price", 0)
        if price > current_price:
            targets_above += 1
            if nearest_above is None or price < nearest_above:
                nearest_above = price
        elif price < current_price:
            targets_below += 1
            if nearest_below is None or price > nearest_below:
                nearest_below = price
    
    # Определяем primary direction
    if targets_above > targets_below * 1.5:
        primary_direction = "up"
    elif targets_below > targets_above * 1.5:
        primary_direction = "down"
    else:
        primary_direction = "neutral"
    
    return {
        "targets_above": targets_above,
        "targets_below": targets_below,
        "primary_direction": primary_direction,
        "nearest_above": nearest_above,
        "nearest_below": nearest_below
    }

