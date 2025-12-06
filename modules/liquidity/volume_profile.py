# modules/liquidity/volume_profile.py

"""
Volume Profile - распределение объёмов по ценовым уровням
Определяет PoC (Point of Control), VAL/VAH (Value Area)
"""

import pandas as pd
import numpy as np


def calculate_volume_profile(df, num_bins=50):
    """
    Рассчитывает Volume Profile из OHLCV данных
    
    Args:
        df: DataFrame с OHLCV
        num_bins: количество ценовых бинов
        
    Returns:
        dict: {
            "poc": float - Point of Control (цена с максимальным объёмом),
            "val": float - Value Area Low (70% объёма),
            "vah": float - Value Area High,
            "profile": dict - полный профиль {price: volume}
        }
    """
    if df.empty or len(df) < 10:
        return {
            "poc": None,
            "val": None,
            "vah": None,
            "profile": {}
        }
    
    # Определяем диапазон цен
    price_min = df['low'].min()
    price_max = df['high'].max()
    
    if price_min >= price_max:
        return {
            "poc": None,
            "val": None,
            "vah": None,
            "profile": {}
        }
    
    # Создаём бины (price bins)
    price_bins = np.linspace(price_min, price_max, num_bins + 1)
    
    # Инициализируем объёмы для каждого бина
    volume_at_price = {float(price_bins[i]): 0.0 for i in range(num_bins)}
    
    # Распределяем объём каждой свечи по бинам
    for idx in range(len(df)):
        candle_low = df['low'].iloc[idx]
        candle_high = df['high'].iloc[idx]
        candle_volume = df['volume'].iloc[idx]
        
        # Находим бины, которые пересекает свеча
        for i in range(num_bins):
            bin_low = price_bins[i]
            bin_high = price_bins[i + 1]
            
            # Проверяем пересечение
            if candle_high >= bin_low and candle_low <= bin_high:
                # Пропорция объёма, попадающая в этот бин
                overlap_low = max(candle_low, bin_low)
                overlap_high = min(candle_high, bin_high)
                overlap_pct = (overlap_high - overlap_low) / (candle_high - candle_low) if candle_high > candle_low else 1.0
                
                volume_at_price[bin_low] += candle_volume * overlap_pct
    
    # Находим PoC (Point of Control) - бин с максимальным объёмом
    poc_price = max(volume_at_price, key=volume_at_price.get)
    poc_volume = volume_at_price[poc_price]
    
    # Сортируем бины по объёму (descending)
    sorted_bins = sorted(volume_at_price.items(), key=lambda x: x[1], reverse=True)
    
    # Находим Value Area (70% объёма)
    total_volume = sum(volume_at_price.values())
    target_volume = total_volume * 0.70
    
    accumulated_volume = 0.0
    value_area_prices = []
    
    for price, volume in sorted_bins:
        if accumulated_volume >= target_volume:
            break
        value_area_prices.append(price)
        accumulated_volume += volume
    
    # VAL и VAH - минимальная и максимальная цены в Value Area
    if value_area_prices:
        val = min(value_area_prices)
        vah = max(value_area_prices)
    else:
        val = None
        vah = None
    
    return {
        "poc": poc_price,
        "poc_volume": poc_volume,
        "val": val,
        "vah": vah,
        "profile": volume_at_price,
        "total_volume": total_volume
    }


def get_position_relative_to_value_area(current_price, volume_profile):
    """
    Определяет положение цены относительно Value Area
    
    Args:
        current_price: текущая цена
        volume_profile: результат calculate_volume_profile
        
    Returns:
        str: "above_vah" | "in_value_area" | "below_val" | "unknown"
    """
    val = volume_profile.get("val")
    vah = volume_profile.get("vah")
    
    if val is None or vah is None:
        return "unknown"
    
    if current_price > vah:
        return "above_vah"  # Цена выше Value Area (бычий признак)
    elif current_price < val:
        return "below_val"  # Цена ниже Value Area (медвежий признак)
    else:
        return "in_value_area"  # Цена в зоне справедливой стоимости


def get_poc_significance(current_price, volume_profile, threshold_pct=0.5):
    """
    Оценивает значимость PoC для текущей цены
    
    Args:
        current_price: текущая цена
        volume_profile: результат calculate_volume_profile
        threshold_pct: порог близости к PoC в процентах
        
    Returns:
        dict: {
            "near_poc": bool,
            "distance_pct": float,
            "poc_acts_as": "support" | "resistance" | "magnet" | None
        }
    """
    poc = volume_profile.get("poc")
    
    if poc is None or current_price is None:
        return {
            "near_poc": False,
            "distance_pct": None,
            "poc_acts_as": None
        }
    
    distance_pct = abs(current_price - poc) / current_price * 100
    near_poc = distance_pct <= threshold_pct
    
    # Определяем роль PoC
    poc_acts_as = None
    if near_poc:
        poc_acts_as = "magnet"  # Цена близко к PoC - "магнит"
    elif current_price > poc:
        poc_acts_as = "support"  # PoC ниже - поддержка
    else:
        poc_acts_as = "resistance"  # PoC выше - сопротивление
    
    return {
        "near_poc": near_poc,
        "distance_pct": distance_pct,
        "poc_acts_as": poc_acts_as
    }

