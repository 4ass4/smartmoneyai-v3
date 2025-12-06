# modules/decision/conflict_detector.py

"""
Детектор конфликтов между модулями анализа
"""

import logging

logger = logging.getLogger(__name__)


class ConflictDetector:
    """
    Определяет конфликты между сигналами разных модулей
    """
    
    def __init__(self, config=None):
        self.config = config
        # Пороги для критичных конфликтов
        self.critical_conflict_threshold = getattr(config, 'CRITICAL_CONFLICT_THRESHOLD', 2) if config else 2
    
    def detect_conflicts(self, signals):
        """
        Анализирует конфликты между модулями
        
        Args:
            signals: Dict со всеми сигналами модулей
            
        Returns:
            dict: {
                "has_conflicts": bool,
                "conflict_count": int,
                "critical_conflicts": int,
                "conflicts": [list of conflicts],
                "severity": "none"|"minor"|"major"|"critical"
            }
        """
        conflicts = []
        critical_count = 0
        
        liq_dir = signals.get("liquidity", {}).get("direction", {}).get("direction", "neutral")
        svd_intent = signals.get("svd", {}).get("intent", "unclear")
        svd_phase = signals.get("svd", {}).get("phase", "discovery")
        trend = signals.get("structure", {}).get("trend", "range")
        ta_trend = signals.get("ta", {}).get("trend", "neutral")
        signal = signals.get("signal", "WAIT")
        
        dom_side = signals.get("svd", {}).get("dom_imbalance", {}).get("side", "neutral")
        thin_above = signals.get("svd", {}).get("thin_zones", {}).get("thin_above", False)
        thin_below = signals.get("svd", {}).get("thin_zones", {}).get("thin_below", False)
        
        # 1. Конфликт: Liquidity vs SVD Intent
        if (liq_dir == "up" and svd_intent == "distributing") or \
           (liq_dir == "down" and svd_intent == "accumulating"):
            conflicts.append({
                "type": "liquidity_vs_svd",
                "severity": "critical",
                "description": f"Ликвидность {liq_dir}, но SVD intent {svd_intent}",
                "recommendation": "WAIT или свип-сценарий"
            })
            critical_count += 1
        
        # 2. Конфликт: Signal vs SVD Intent
        if (signal == "BUY" and svd_intent == "distributing") or \
           (signal == "SELL" and svd_intent == "accumulating"):
            conflicts.append({
                "type": "signal_vs_svd",
                "severity": "critical",
                "description": f"Сигнал {signal}, но SVD intent {svd_intent}",
                "recommendation": "WAIT - сильное противоречие"
            })
            critical_count += 1
        
        # 3. Конфликт: Signal vs DOM
        if (signal == "BUY" and dom_side == "ask") or \
           (signal == "SELL" and dom_side == "bid"):
            conflicts.append({
                "type": "signal_vs_dom",
                "severity": "major",
                "description": f"Сигнал {signal}, но DOM давит в обратную сторону ({dom_side})",
                "recommendation": "Осторожность - DOM против сигнала"
            })
        
        # 4. Конфликт: Signal vs Thin Zones
        if (signal == "BUY" and thin_below and not thin_above) or \
           (signal == "SELL" and thin_above and not thin_below):
            conflicts.append({
                "type": "signal_vs_thin",
                "severity": "major",
                "description": f"Сигнал {signal}, но тонкая ликвидность в противоположную сторону",
                "recommendation": "Риск быстрого движения против сигнала"
            })
        
        # 5. Конфликт: Trend vs TA Trend
        if (trend == "bullish" and ta_trend == "bearish") or \
           (trend == "bearish" and ta_trend == "bullish"):
            conflicts.append({
                "type": "structure_vs_ta",
                "severity": "minor",
                "description": f"Структура {trend}, но TA {ta_trend}",
                "recommendation": "Возможная смена тренда"
            })
        
        # 6. Конфликт: Phase не execution, но сигнал агрессивный
        if svd_phase not in ("execution", "distribution") and signal in ("BUY", "SELL"):
            conflicts.append({
                "type": "phase_vs_signal",
                "severity": "major",
                "description": f"Фаза {svd_phase}, но генерируется сигнал {signal}",
                "recommendation": "Ждать фазы execution для подтверждения"
            })
        
        # 7. Конфликт: HTF против локального тренда
        htf1 = signals.get("htf", {}).get("htf1", "unknown")
        htf2 = signals.get("htf", {}).get("htf2", "unknown")
        if (trend == "bullish" and htf1 == "bearish") or \
           (trend == "bearish" and htf1 == "bullish"):
            conflicts.append({
                "type": "ltf_vs_htf",
                "severity": "minor",
                "description": f"Локальный тренд {trend}, но HTF {htf1}",
                "recommendation": "HTF может подавить локальный тренд"
            })
        
        # Определяем общую severity
        if critical_count >= self.critical_conflict_threshold:
            severity = "critical"
        elif critical_count > 0:
            severity = "major"
        elif len(conflicts) >= 3:
            severity = "major"
        elif len(conflicts) > 0:
            severity = "minor"
        else:
            severity = "none"
        
        has_conflicts = len(conflicts) > 0
        
        if has_conflicts:
            logger.warning(f"⚠️ Обнаружено конфликтов: {len(conflicts)} (критичных: {critical_count}, severity: {severity})")
            for conf in conflicts:
                logger.warning(f"   - {conf['type']}: {conf['description']}")
        
        return {
            "has_conflicts": has_conflicts,
            "conflict_count": len(conflicts),
            "critical_conflicts": critical_count,
            "conflicts": conflicts,
            "severity": severity
        }
    
    def should_force_wait(self, conflict_result):
        """
        Определяет, нужно ли форсировать WAIT из-за конфликтов
        
        Args:
            conflict_result: результат detect_conflicts
            
        Returns:
            tuple: (should_wait: bool, reason: str)
        """
        severity = conflict_result["severity"]
        critical_count = conflict_result["critical_conflicts"]
        
        # Критичные конфликты - всегда WAIT
        if severity == "critical":
            reason = f"Критичные конфликты ({critical_count}): " + ", ".join([c["type"] for c in conflict_result["conflicts"] if c["severity"] == "critical"])
            return (True, reason)
        
        # Major конфликты при низкой уверенности - WAIT
        # (это будет проверено в decision_engine с учетом confidence)
        
        return (False, "")

