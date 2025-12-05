# modules/utils/math_tools.py

import numpy as np


def calculate_percentage_change(old_value, new_value):
    """Расчет процентного изменения"""
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100


def normalize_value(value, min_val, max_val):
    """Нормализация значения в диапазон 0-1"""
    if max_val == min_val:
        return 0
    return (value - min_val) / (max_val - min_val)


def calculate_distance(price1, price2):
    """Расчет расстояния между ценами в процентах"""
    if price1 == 0:
        return 0
    return abs((price2 - price1) / price1) * 100

