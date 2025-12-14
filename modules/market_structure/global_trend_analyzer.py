# modules/market_structure/global_trend_analyzer.py

"""
Анализатор глобального тренда на основе HTF данных
Определяет общее направление рынка на больших таймфреймах
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class GlobalTrendAnalyzer:
    """
    Анализирует глобальный тренд на основе нескольких таймфреймов
    """
    
    def __init__(self):
        pass
    
    def analyze_global_trend(self, htf1_data, htf2_data, htf1_phases=None, htf2_phases=None):
        """
        Анализирует глобальный тренд на основе HTF данных
        
        Args:
            htf1_data: данные структуры рынка для HTF1 (1h)
            htf2_data: данные структуры рынка для HTF2 (4h)
            htf1_phases: исторические фазы для HTF1 (опционально)
            htf2_phases: исторические фазы для HTF2 (опционально)
        
        Returns:
            dict: {
                "global_direction": "up" | "down" | "neutral",
                "global_trend_strength": 0.0-1.0,
                "htf1_trend": "bullish" | "bearish" | "range",
                "htf2_trend": "bullish" | "bearish" | "range",
                "htf1_phase": "accumulation" | "distribution" | "neutral",
                "htf2_phase": "accumulation" | "distribution" | "neutral",
                "consensus": "strong_up" | "up" | "neutral" | "down" | "strong_down",
                "trend_alignment": 0.0-1.0,  # Насколько совпадают тренды на разных ТФ
                "recommendation": str  # Текстовое описание
            }
        """
        # Извлекаем тренды
        htf1_trend = htf1_data.get("trend", "range") if htf1_data else "unknown"
        htf2_trend = htf2_data.get("trend", "range") if htf2_data else "unknown"
        
        # Извлекаем фазы накопления/распределения
        htf1_phase = htf1_phases.get("global_trend", "neutral") if htf1_phases else "neutral"
        htf2_phase = htf2_phases.get("global_trend", "neutral") if htf2_phases else "neutral"
        
        # Определяем глобальное направление
        global_direction, global_strength = self._determine_global_direction(
            htf1_trend, htf2_trend, htf1_phase, htf2_phase
        )
        
        # Консенсус между таймфреймами
        consensus = self._calculate_consensus(htf1_trend, htf2_trend, htf1_phase, htf2_phase)
        
        # Выравнивание трендов
        trend_alignment = self._calculate_trend_alignment(htf1_trend, htf2_trend, htf1_phase, htf2_phase)
        
        # Рекомендация
        recommendation = self._generate_recommendation(
            global_direction, global_strength, consensus, htf1_phase, htf2_phase
        )
        
        result = {
            "global_direction": global_direction,
            "global_trend_strength": global_strength,
            "htf1_trend": htf1_trend,
            "htf2_trend": htf2_trend,
            "htf1_phase": htf1_phase,
            "htf2_phase": htf2_phase,
            "consensus": consensus,
            "trend_alignment": trend_alignment,
            "recommendation": recommendation
        }
        
        logger.info(f"🌍 Global Trend: {global_direction} (strength: {global_strength:.2f}, consensus: {consensus})")
        
        return result
    
    def _determine_global_direction(self, htf1_trend, htf2_trend, htf1_phase, htf2_phase):
        """
        Определяет глобальное направление на основе трендов и фаз
        """
        # Веса для разных таймфреймов (4h важнее чем 1h)
        htf2_weight = 0.6
        htf1_weight = 0.4
        
        # Оценка направления по трендам
        trend_score = 0.0
        if htf2_trend == "bullish":
            trend_score += htf2_weight
        elif htf2_trend == "bearish":
            trend_score -= htf2_weight
        
        if htf1_trend == "bullish":
            trend_score += htf1_weight
        elif htf1_trend == "bearish":
            trend_score -= htf1_weight
        
        # Оценка направления по фазам
        phase_score = 0.0
        if htf2_phase == "accumulation":
            phase_score += htf2_weight * 0.5
        elif htf2_phase == "distribution":
            phase_score -= htf2_weight * 0.5
        
        if htf1_phase == "accumulation":
            phase_score += htf1_weight * 0.5
        elif htf1_phase == "distribution":
            phase_score -= htf1_weight * 0.5
        
        # Комбинируем (тренды важнее фаз)
        total_score = trend_score * 0.7 + phase_score * 0.3
        
        # Определяем направление
        if total_score > 0.3:
            direction = "up"
            strength = min(1.0, total_score)
        elif total_score < -0.3:
            direction = "down"
            strength = min(1.0, abs(total_score))
        else:
            direction = "neutral"
            strength = 1.0 - abs(total_score)
        
        return direction, strength
    
    def _calculate_consensus(self, htf1_trend, htf2_trend, htf1_phase, htf2_phase):
        """
        Рассчитывает консенсус между таймфреймами
        """
        # Проверяем совпадение трендов
        trend_match = (htf1_trend == htf2_trend) and (htf1_trend in ("bullish", "bearish"))
        
        # Проверяем совпадение фаз
        phase_match = (htf1_phase == htf2_phase) and (htf1_phase in ("accumulation", "distribution"))
        
        # Если оба совпадают
        if trend_match and phase_match:
            if htf1_trend == "bullish" and htf1_phase == "accumulation":
                return "strong_up"
            elif htf1_trend == "bearish" and htf1_phase == "distribution":
                return "strong_down"
        
        # Если тренды совпадают
        if trend_match:
            if htf1_trend == "bullish":
                return "up"
            else:
                return "down"
        
        # Если фазы совпадают
        if phase_match:
            if htf1_phase == "accumulation":
                return "up"
            else:
                return "down"
        
        # Противоречие
        return "neutral"
    
    def _calculate_trend_alignment(self, htf1_trend, htf2_trend, htf1_phase, htf2_phase):
        """
        Рассчитывает выравнивание трендов (0-1, где 1 = полное совпадение)
        """
        alignment = 0.0
        
        # Выравнивание трендов (0.5 веса)
        if htf1_trend == htf2_trend:
            if htf1_trend in ("bullish", "bearish"):
                alignment += 0.5
        elif htf1_trend == "range" or htf2_trend == "range":
            alignment += 0.25  # Частичное совпадение
        
        # Выравнивание фаз (0.5 веса)
        if htf1_phase == htf2_phase:
            if htf1_phase in ("accumulation", "distribution"):
                alignment += 0.5
        elif htf1_phase == "neutral" or htf2_phase == "neutral":
            alignment += 0.25  # Частичное совпадение
        
        return alignment
    
    def _generate_recommendation(self, global_direction, strength, consensus, htf1_phase, htf2_phase):
        """
        Генерирует текстовую рекомендацию
        """
        if consensus == "strong_up":
            return f"🔥 СИЛЬНЫЙ ВОСХОДЯЩИЙ ТРЕНД: На всех таймфреймах (1h/4h) наблюдается накопление и бычий тренд. Глобальное направление: ВВЕРХ (сила: {strength:.0%})"
        elif consensus == "strong_down":
            return f"📉 СИЛЬНЫЙ НИСХОДЯЩИЙ ТРЕНД: На всех таймфреймах (1h/4h) наблюдается распределение и медвежий тренд. Глобальное направление: ВНИЗ (сила: {strength:.0%})"
        elif consensus == "up":
            return f"📈 ВОСХОДЯЩИЙ ТРЕНД: Преобладает накопление на HTF. Глобальное направление: ВВЕРХ (сила: {strength:.0%})"
        elif consensus == "down":
            return f"📉 НИСХОДЯЩИЙ ТРЕНД: Преобладает распределение на HTF. Глобальное направление: ВНИЗ (сила: {strength:.0%})"
        elif global_direction == "up":
            return f"📈 СЛАБЫЙ ВОСХОДЯЩИЙ ТРЕНД: Есть признаки накопления, но не на всех таймфреймах. Глобальное направление: ВВЕРХ (сила: {strength:.0%})"
        elif global_direction == "down":
            return f"📉 СЛАБЫЙ НИСХОДЯЩИЙ ТРЕНД: Есть признаки распределения, но не на всех таймфреймах. Глобальное направление: ВНИЗ (сила: {strength:.0%})"
        else:
            return f"⚪ НЕЙТРАЛЬНЫЙ РЫНОК: Противоречивые сигналы на разных таймфреймах. Глобальное направление: НЕЙТРАЛЬНО (сила: {strength:.0%})"

