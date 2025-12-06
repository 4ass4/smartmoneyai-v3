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
    
    def mark_as_swept(self, price, direction, reason="sweep"):
        """
        Помечает уровень как swept (отработанный)
        
        Args:
            price: цена уровня
            direction: "up" (swept вверх) или "down" (swept вниз)
            reason: причина (sweep, liquidation, breakout)
        """
        timestamp = time.time()
        
        # Проверяем, нет ли уже такого уровня (в пределах 0.1%)
        for level in self.swept_levels:
            if abs(level["price"] - price) / price < 0.001:  # < 0.1%
                # Обновляем timestamp (уровень swept повторно)
                level["timestamp"] = timestamp
                level["count"] = level.get("count", 1) + 1
                return
        
        # Добавляем новый swept уровень
        self.swept_levels.append({
            "price": price,
            "direction": direction,
            "timestamp": timestamp,
            "reason": reason,
            "count": 1
        })
    
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

