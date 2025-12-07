# modules/utils/healthcheck.py

"""
Healthcheck и мониторинг системы
"""

import time
import psutil
import logging
from collections import deque

logger = logging.getLogger(__name__)


class HealthMonitor:
    """
    Мониторинг здоровья системы и метрик
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.last_signal_time = None
        self.signal_count = 0
        self.error_count = 0
        self.api_call_count = 0
        self.api_error_count = 0
        self.ws_reconnect_count = 0
        
        # История последних метрик
        self.metrics_history = deque(maxlen=100)
        
        # Счетчики по типам сигналов
        self.signal_types = {"BUY": 0, "SELL": 0, "WAIT": 0}
    
    def uptime_seconds(self):
        """Возвращает время работы в секундах"""
        return time.time() - self.start_time
    
    def record_signal(self, signal_type):
        """Записывает новый сигнал"""
        self.last_signal_time = time.time()
        self.signal_count += 1
        if signal_type in self.signal_types:
            self.signal_types[signal_type] += 1
    
    def record_error(self):
        """Записывает ошибку"""
        self.error_count += 1
    
    def record_api_call(self, success=True):
        """Записывает API вызов"""
        self.api_call_count += 1
        if not success:
            self.api_error_count += 1
    
    def record_ws_reconnect(self):
        """Записывает переподключение WebSocket"""
        self.ws_reconnect_count += 1
    
    def get_system_metrics(self):
        """Возвращает системные метрики (CPU, память)"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024)
            }
        except Exception as e:
            logger.error(f"Ошибка получения системных метрик: {e}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "memory_available_mb": 0
            }
    
    def get_status(self):
        """
        Возвращает полный статус системы
        
        Returns:
            dict: {
                "status": "healthy"|"degraded"|"unhealthy",
                "uptime_seconds": float,
                "uptime_hours": float,
                "last_signal_seconds_ago": float,
                "signal_count": int,
                "signal_types": dict,
                "error_count": int,
                "api_success_rate": float,
                "ws_reconnects": int,
                "system": dict
            }
        """
        uptime = self.uptime_seconds()
        last_signal_ago = (time.time() - self.last_signal_time) if self.last_signal_time else None
        
        # Рассчитываем success rate API
        api_success_rate = 1.0
        if self.api_call_count > 0:
            api_success_rate = 1.0 - (self.api_error_count / self.api_call_count)
        
        # Системные метрики
        system_metrics = self.get_system_metrics()
        
        # Определяем статус
        status = "healthy"
        
        # Unhealthy если:
        # - Нет сигналов больше 10 минут
        # - Много ошибок API (success rate < 50%)
        # - Много переподключений WS (> 50)
        if last_signal_ago and last_signal_ago > 600:
            status = "unhealthy"
            logger.warning(f"⚠️ Unhealthy: Нет сигналов {last_signal_ago:.0f}s")
        elif api_success_rate < 0.5:
            status = "unhealthy"
            logger.warning(f"⚠️ Unhealthy: API success rate {api_success_rate:.1%}")
        elif self.ws_reconnect_count > 50:
            status = "unhealthy"
            logger.warning(f"⚠️ Unhealthy: WS reconnects {self.ws_reconnect_count}")
        
        # Degraded если:
        # - Нет сигналов больше 5 минут
        # - Успешность API 50-80%
        # - Много переподключений WS (> 20)
        elif last_signal_ago and last_signal_ago > 300:
            status = "degraded"
        elif api_success_rate < 0.8:
            status = "degraded"
        elif self.ws_reconnect_count > 20:
            status = "degraded"
        
        return {
            "status": status,
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "last_signal_seconds_ago": last_signal_ago,
            "signal_count": self.signal_count,
            "signal_types": self.signal_types,
            "error_count": self.error_count,
            "api_calls": self.api_call_count,
            "api_errors": self.api_error_count,
            "api_success_rate": api_success_rate,
            "ws_reconnects": self.ws_reconnect_count,
            "system": system_metrics
        }
    
    def log_status(self):
        """Логирует текущий статус"""
        status = self.get_status()
        status_icon = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌"
        }
        icon = status_icon.get(status["status"], "❓")
        
        logger.info(f"{icon} Status: {status['status']}, Uptime: {status['uptime_hours']:.1f}h, Signals: {status['signal_count']}, API Success: {status['api_success_rate']:.1%}")




