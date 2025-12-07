# modules/alerts/alert_manager.py

"""
Менеджер алертов для важных событий рынка
Оповещает о критических изменениях: смена фазы, разворот CVD, и т.д.
"""

import logging
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Управляет алертами о важных событиях
    """
    
    def __init__(self):
        self.last_alerts = deque(maxlen=50)  # История последних алертов
        self.last_phase = None
        self.last_cvd_intent = None
        self.last_execution_alert_time = None
        self.cooldown_minutes = 15  # Минимум 15 минут между похожими алертами
    
    def check_phase_change(self, current_phase, phase_info):
        """
        Проверяет смену фазы и генерирует алерт
        
        Args:
            current_phase: текущая фаза (manipulation/execution/distribution/discovery)
            phase_info: полная информация о фазе
        
        Returns:
            dict: алерт или None
        """
        if self.last_phase is None:
            self.last_phase = current_phase
            return None
        
        if current_phase != self.last_phase:
            # Смена фазы обнаружена!
            alert = {
                "type": "phase_change",
                "severity": "high" if current_phase in ("execution", "distribution") else "medium",
                "from_phase": self.last_phase,
                "to_phase": current_phase,
                "duration": phase_info.get("phase_duration_s", 0),
                "timestamp": datetime.now(),
                "message": self._generate_phase_change_message(self.last_phase, current_phase, phase_info)
            }
            
            self.last_phase = current_phase
            self.last_alerts.append(alert)
            
            logger.warning(f"🚨 АЛЕРТ: Смена фазы {self.last_phase} → {current_phase}")
            
            return alert
        
        return None
    
    def check_cvd_reversal(self, svd_data):
        """
        Проверяет разворот CVD и генерирует алерт
        
        Args:
            svd_data: данные SVD engine
        
        Returns:
            dict: алерт или None
        """
        cvd_reversal = svd_data.get("cvd_reversal_detected", False)
        current_intent = svd_data.get("intent", "unclear")
        cvd_value = svd_data.get("cvd", 0)
        cvd_slope = svd_data.get("cvd_slope", 0)
        
        # Проверяем смену intent
        if self.last_cvd_intent and current_intent != self.last_cvd_intent:
            if current_intent in ("accumulating", "distributing"):
                alert = {
                    "type": "cvd_intent_change",
                    "severity": "high",
                    "from_intent": self.last_cvd_intent,
                    "to_intent": current_intent,
                    "cvd_value": cvd_value,
                    "cvd_slope": cvd_slope,
                    "reversal": cvd_reversal,
                    "timestamp": datetime.now(),
                    "message": self._generate_cvd_change_message(
                        self.last_cvd_intent, current_intent, cvd_value, cvd_slope
                    )
                }
                
                self.last_cvd_intent = current_intent
                self.last_alerts.append(alert)
                
                logger.warning(f"🚨 АЛЕРТ: CVD Intent {self.last_cvd_intent} → {current_intent}")
                
                return alert
        
        self.last_cvd_intent = current_intent
        
        # Проверяем обнаружение разворота
        if cvd_reversal:
            alert = {
                "type": "cvd_reversal",
                "severity": "high",
                "intent": current_intent,
                "cvd_value": cvd_value,
                "cvd_slope": cvd_slope,
                "timestamp": datetime.now(),
                "message": f"🔄 РАЗВОРОТ ТРЕНДА: CVD={cvd_value:.1f}, slope={cvd_slope:.1f} → {current_intent}"
            }
            
            self.last_alerts.append(alert)
            logger.warning(f"🚨 АЛЕРТ: CVD разворот обнаружен!")
            
            return alert
        
        return None
    
    def check_execution_phase(self, phase, svd_data, signal_data):
        """
        Проверяет execution фазу и генерирует алерт
        
        Args:
            phase: текущая фаза
            svd_data: данные SVD
            signal_data: данные сигнала
        
        Returns:
            dict: алерт или None
        """
        if phase != "execution":
            return None
        
        # Cooldown для execution алертов
        if self.last_execution_alert_time:
            elapsed = (datetime.now() - self.last_execution_alert_time).total_seconds() / 60
            if elapsed < self.cooldown_minutes:
                return None
        
        cvd_value = svd_data.get("cvd", 0)
        intent = svd_data.get("intent", "unclear")
        confidence = signal_data.get("confidence", 0)
        
        alert = {
            "type": "execution_phase",
            "severity": "critical",
            "phase": phase,
            "intent": intent,
            "cvd": cvd_value,
            "confidence": confidence,
            "timestamp": datetime.now(),
            "message": self._generate_execution_message(intent, cvd_value, confidence)
        }
        
        self.last_execution_alert_time = datetime.now()
        self.last_alerts.append(alert)
        
        logger.warning(f"🚨 АЛЕРТ: EXECUTION ФАЗА! Intent: {intent}, CVD: {cvd_value:.1f}")
        
        return alert
    
    def check_strong_signal(self, signal_data):
        """
        Проверяет сильный сигнал (confidence >= 7.0)
        
        Args:
            signal_data: данные сигнала
        
        Returns:
            dict: алерт или None
        """
        direction = signal_data.get("direction", "WAIT")
        confidence = signal_data.get("confidence", 0)
        
        if direction in ("BUY", "SELL") and confidence >= 7.0:
            alert = {
                "type": "strong_signal",
                "severity": "high",
                "direction": direction,
                "confidence": confidence,
                "timestamp": datetime.now(),
                "message": f"📊 СИЛЬНЫЙ СИГНАЛ: {direction} (уверенность: {confidence:.1f}/10)"
            }
            
            self.last_alerts.append(alert)
            logger.warning(f"🚨 АЛЕРТ: Сильный сигнал {direction} ({confidence:.1f}/10)")
            
            return alert
        
        return None
    
    def _generate_phase_change_message(self, from_phase, to_phase, phase_info):
        """Генерирует сообщение о смене фазы"""
        duration = phase_info.get("phase_duration_s", 0)
        duration_min = duration / 60
        
        messages = {
            ("manipulation", "execution"): f"⚡ EXECUTION НАЧАЛАСЬ! (после {duration_min:.1f}м манипуляций)",
            ("execution", "distribution"): f"📉 DISTRIBUTION: Киты завершили покупки (execution длился {duration_min:.1f}м)",
            ("distribution", "manipulation"): f"🔄 Новый цикл: distribution → manipulation",
            ("manipulation", "distribution"): f"📉 DISTRIBUTION: Пропущена execution фаза?",
        }
        
        key = (from_phase, to_phase)
        return messages.get(key, f"🔄 Смена фазы: {from_phase} → {to_phase}")
    
    def _generate_cvd_change_message(self, from_intent, to_intent, cvd_value, cvd_slope):
        """Генерирует сообщение о смене CVD intent"""
        messages = {
            ("accumulating", "distributing"): f"🔴 КИТЫ НАЧАЛИ ПРОДАВАТЬ! CVD: {cvd_value:.1f}, slope: {cvd_slope:.1f}",
            ("distributing", "accumulating"): f"🟢 КИТЫ НАЧАЛИ ПОКУПАТЬ! CVD: {cvd_value:.1f}, slope: {cvd_slope:.1f}",
        }
        
        key = (from_intent, to_intent)
        return messages.get(key, f"🔄 CVD Intent: {from_intent} → {to_intent}")
    
    def _generate_execution_message(self, intent, cvd_value, confidence):
        """Генерирует сообщение об execution фазе"""
        if intent == "accumulating":
            return f"⚡ EXECUTION: Киты покупают! CVD: {cvd_value:.1f}, confidence: {confidence:.1f}/10"
        elif intent == "distributing":
            return f"⚡ EXECUTION: Киты продают! CVD: {cvd_value:.1f}, confidence: {confidence:.1f}/10"
        else:
            return f"⚡ EXECUTION ФАЗА! CVD: {cvd_value:.1f}"
    
    def get_recent_alerts(self, minutes=60, severity=None):
        """
        Получает недавние алерты
        
        Args:
            minutes: за последние N минут
            severity: фильтр по severity (critical/high/medium/low)
        
        Returns:
            list: список алертов
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent = [
            alert for alert in self.last_alerts
            if alert["timestamp"] >= cutoff_time
        ]
        
        if severity:
            recent = [a for a in recent if a["severity"] == severity]
        
        return recent
    
    def format_alert_for_telegram(self, alert):
        """
        Форматирует алерт для Telegram
        
        Args:
            alert: алерт
        
        Returns:
            str: форматированное сообщение
        """
        severity_emoji = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "ℹ️",
            "low": "💡"
        }
        
        emoji = severity_emoji.get(alert["severity"], "📢")
        message = alert["message"]
        timestamp = alert["timestamp"].strftime("%H:%M:%S")
        
        return f"{emoji} [{timestamp}] {message}"

