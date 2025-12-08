# modules/liquidity/swept_tracker.py

"""
Трекер отработанных (swept) уровней ликвидности
Помечает уровни, которые были swept, чтобы не использовать их повторно
"""

import time


class SweptLevelsTracker:
    """
    Отслеживает swept (отработанные) уровни ликвидности
    """
    
    def __init__(self, expiry_hours=24):
        """
        Args:
            expiry_hours: через сколько часов swept уровень "забывается"
        """
        self.swept_levels = []  # [{price, direction, timestamp, reason}]
        self.expiry_seconds = expiry_hours * 3600
    
    def mark_as_swept(self, price, direction, reason="sweep", candles_ago=None):
        """
        Помечает уровень как swept (отработанный)
        
        Args:
            price: цена уровня
            direction: "up" (swept вверх) или "down" (swept вниз)
            reason: причина (sweep, liquidation, breakout, historical_sweep_...)
            candles_ago: сколько свечей назад был sweep (для исторических sweeps)
        """
        timestamp = time.time()
        
        # Проверяем, нет ли уже такого уровня (в пределах 0.1%)
        for level in self.swept_levels:
            if abs(level["price"] - price) / price < 0.001:  # < 0.1%
                # КРИТИЧНО: НЕ инкрементируем count если это дубликат из того же цикла!
                # Инкрементируем только если прошло > 60 секунд с последнего обновления
                time_since_last = timestamp - level.get("timestamp", 0)
                
                if time_since_last < 60:  # < 1 минуты
                    # Это дубликат из того же цикла анализа - игнорируем
                    return
                
                # Прошло > 1 минуты - это НОВЫЙ sweep того же уровня
                level["timestamp"] = timestamp
                level["count"] = level.get("count", 1) + 1
                if candles_ago and "candles_ago" not in level:
                    level["candles_ago"] = candles_ago
                return
        
        # Добавляем новый swept уровень
        swept_level = {
            "price": price,
            "direction": direction,
            "timestamp": timestamp,
            "reason": reason,
            "count": 1
        }
        
        if candles_ago:
            swept_level["candles_ago"] = candles_ago
        
        self.swept_levels.append(swept_level)
    
    def is_swept(self, price, tolerance_pct=0.5):
        """
        Проверяет, является ли уровень swept
        
        Args:
            price: цена уровня
            tolerance_pct: допуск в процентах (если уровень в пределах tolerance от swept - считается swept)
            
        Returns:
            bool: True если уровень swept
        """
        self._cleanup_expired()
        
        for level in self.swept_levels:
            if abs(level["price"] - price) / price * 100 < tolerance_pct:
                return True
        return False
    
    def get_swept_info(self, price, tolerance_pct=0.5):
        """
        Получает информацию о swept уровне
        
        Returns:
            dict или None
        """
        self._cleanup_expired()
        
        for level in self.swept_levels:
            if abs(level["price"] - price) / price * 100 < tolerance_pct:
                return level
        return None
    
    def filter_swept_levels(self, levels, tolerance_pct=0.5):
        """
        Фильтрует список уровней, исключая swept
        
        Args:
            levels: list of dict с ключом "price"
            tolerance_pct: допуск в процентах
            
        Returns:
            list: отфильтрованные уровни (только не-swept)
        """
        self._cleanup_expired()
        
        filtered = []
        for level in levels:
            price = level.get("price")
            if price is None:
                continue
            
            if not self.is_swept(price, tolerance_pct):
                filtered.append(level)
        
        return filtered
    
    def get_all_swept(self):
        """Возвращает все активные swept уровни"""
        self._cleanup_expired()
        return self.swept_levels.copy()
    
    def _cleanup_expired(self):
        """Удаляет устаревшие swept уровни"""
        current_time = time.time()
        self.swept_levels = [
            level for level in self.swept_levels
            if (current_time - level["timestamp"]) < self.expiry_seconds
        ]
    
    def reset(self):
        """Очищает все swept уровни"""
        self.swept_levels = []

