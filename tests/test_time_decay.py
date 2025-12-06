# tests/test_time_decay.py

"""
Unit тесты для time_decay
"""

import pytest
import time
from modules.utils.time_decay import calculate_time_decay, apply_decay_to_levels, get_weighted_importance


class TestTimeDecay:
    def test_fresh_level(self):
        """Тест: свежий уровень имеет decay ~1.0"""
        current_ts = int(time.time() * 1000)
        level_ts = current_ts - 1000  # 1 секунда назад
        
        decay = calculate_time_decay(level_ts, current_ts, half_life_seconds=86400)
        
        assert decay > 0.99
    
    def test_old_level(self):
        """Тест: старый уровень имеет низкий decay"""
        current_ts = int(time.time() * 1000)
        level_ts = current_ts - (86400 * 5 * 1000)  # 5 дней назад
        
        decay = calculate_time_decay(level_ts, current_ts, half_life_seconds=86400)
        
        assert decay < 0.1
    
    def test_half_life_decay(self):
        """Тест: через half_life decay = 0.5"""
        current_ts = int(time.time() * 1000)
        half_life = 3600  # 1 час
        level_ts = current_ts - (half_life * 1000)  # ровно half_life назад
        
        decay = calculate_time_decay(level_ts, current_ts, half_life_seconds=half_life)
        
        assert 0.49 < decay < 0.51
    
    def test_apply_decay_to_levels(self):
        """Тест: применение decay к списку уровней"""
        current_ts = int(time.time() * 1000)
        
        levels = [
            {"price": 100.0, "timestamp": current_ts - 1000},  # свежий
            {"price": 101.0, "timestamp": current_ts - 86400000},  # 1 день
            {"price": 102.0, "timestamp": current_ts - 86400000 * 3}  # 3 дня
        ]
        
        result = apply_decay_to_levels(levels, current_ts, half_life_seconds=86400)
        
        assert result[0]["decay_weight"] > 0.99  # свежий
        assert result[1]["decay_weight"] < 0.6  # 1 день
        assert result[2]["decay_weight"] < 0.2  # 3 дня
    
    def test_weighted_importance(self):
        """Тест: взвешенная важность"""
        base_importance = 100.0
        decay_weight = 0.5
        
        weighted = get_weighted_importance(base_importance, decay_weight)
        
        assert weighted == 50.0
    
    def test_no_timestamp(self):
        """Тест: уровень без timestamp получает средний decay"""
        decay = calculate_time_decay(None, int(time.time() * 1000))
        
        assert decay == 0.5

