# modules/svd/phase_tracker.py

"""
Трекинг последовательности фаз Smart Money:
discovery → manipulation → execution → distribution
"""

import logging
from collections import deque

logger = logging.getLogger(__name__)


class PhaseTracker:
    """
    Отслеживает последовательность фаз и переходы между ними
    """
    
    def __init__(self, history_size=10):
        self.history_size = history_size
        self.phase_history = deque(maxlen=history_size)
        self.current_phase = "discovery"
        self.phase_start_time = None
        self.phase_duration = 0
    
    def update_phase(self, new_phase, timestamp=None):
        """
        Обновляет текущую фазу и проверяет логичность перехода
        
        Args:
            new_phase: новая фаза
            timestamp: timestamp текущего момента (ms)
            
        Returns:
            dict: {
                "phase": current_phase,
                "phase_changed": bool,
                "phase_duration_seconds": float,
                "is_valid_transition": bool,
                "phase_confidence": float  # 0-1, насколько уверены в фазе
            }
        """
        import time
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        phase_changed = (new_phase != self.current_phase)
        
        # Рассчитываем длительность текущей фазы
        if self.phase_start_time:
            self.phase_duration = (timestamp - self.phase_start_time) / 1000
        else:
            self.phase_duration = 0
        
        # Проверяем валидность перехода
        is_valid_transition = self._is_valid_transition(self.current_phase, new_phase)
        
        if phase_changed:
            logger.info(f"🔄 Смена фазы: {self.current_phase} → {new_phase} (длительность: {self.phase_duration:.1f}s, valid: {is_valid_transition})")
            
            # Добавляем в историю
            self.phase_history.append({
                "phase": self.current_phase,
                "duration_seconds": self.phase_duration,
                "timestamp": timestamp
            })
            
            # Обновляем текущую фазу
            self.current_phase = new_phase
            self.phase_start_time = timestamp
        
        # Рассчитываем confidence фазы на основе истории
        phase_confidence = self._calculate_phase_confidence()
        
        return {
            "phase": self.current_phase,
            "phase_changed": phase_changed,
            "phase_duration_seconds": self.phase_duration,
            "is_valid_transition": is_valid_transition,
            "phase_confidence": phase_confidence,
            "phase_history": list(self.phase_history)
        }
    
    def _is_valid_transition(self, from_phase, to_phase):
        """
        Проверяет, является ли переход между фазами логичным
        
        Valid transitions:
        discovery → manipulation
        manipulation → execution
        execution → distribution
        distribution → discovery (новый цикл)
        
        discovery → execution (возможно, но менее типично)
        manipulation → distribution (пропуск execution)
        """
        if from_phase == to_phase:
            return True  # Оставаться в той же фазе валидно
        
        # Типичные переходы
        typical_transitions = {
            "discovery": ["manipulation", "execution"],
            "manipulation": ["execution", "distribution"],
            "execution": ["distribution"],
            "distribution": ["discovery"]
        }
        
        return to_phase in typical_transitions.get(from_phase, [])
    
    def _calculate_phase_confidence(self):
        """
        Рассчитывает уверенность в текущей фазе на основе истории
        
        Returns:
            float: 0-1
        """
        if len(self.phase_history) < 2:
            return 0.5  # Недостаточно истории
        
        # Проверяем последовательность: если последние переходы были валидны - выше confidence
        valid_count = 0
        total_count = 0
        
        for i in range(len(self.phase_history) - 1):
            from_p = self.phase_history[i]["phase"]
            to_p = self.phase_history[i + 1]["phase"]
            if self._is_valid_transition(from_p, to_p):
                valid_count += 1
            total_count += 1
        
        if total_count == 0:
            return 0.5
        
        # Confidence = доля валидных переходов
        confidence = valid_count / total_count
        
        # Бонус, если текущая фаза держится достаточно долго (не "шум")
        if self.phase_duration > 60:  # более 1 минуты
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def get_expected_next_phase(self):
        """
        Возвращает ожидаемую следующую фазу на основе текущей
        
        Returns:
            list: список возможных следующих фаз
        """
        transitions = {
            "discovery": ["manipulation", "execution"],
            "manipulation": ["execution"],
            "execution": ["distribution"],
            "distribution": ["discovery"]
        }
        
        return transitions.get(self.current_phase, [])
    
    def is_in_cycle(self):
        """
        Проверяет, прошли ли мы полный цикл (discovery → ... → distribution)
        
        Returns:
            bool: True если за последние N фаз был полный цикл
        """
        if len(self.phase_history) < 4:
            return False
        
        # Ищем последовательность discovery → manipulation → execution → distribution
        phases = [h["phase"] for h in self.phase_history]
        
        # Простая проверка: есть ли все 4 фазы в последних записях
        required_phases = {"discovery", "manipulation", "execution", "distribution"}
        recent_phases = set(phases[-6:])  # Последние 6 записей
        
        return required_phases.issubset(recent_phases)




