# modules/behavior/behavior_engine.py

"""
Behavior Engine - анализ поведения толпы vs крупных игроков (китов)
Агрегирует все признаки эмоций толпы и действий китов
"""

import logging

logger = logging.getLogger(__name__)


class BehaviorEngine:
    """
    Анализирует поведение толпы и китов
    """
    
    def __init__(self, config=None):
        self.config = config
    
    def analyze(self, svd_data, trap_data, liquidity_data):
        """
        Анализирует поведение толпы и китов на основе всех данных
        
        Args:
            svd_data: данные от SVDEngine
            trap_data: данные от TrapEngine
            liquidity_data: данные от LiquidityEngine
            
        Returns:
            dict: {
                "crowd_sentiment": "fearful" | "greedy" | "neutral" | "panic" | "fomo",
                "crowd_trapped": bool,
                "whale_action": "accumulating" | "distributing" | "manipulating" | "inactive",
                "whale_confidence": float (0-10),
                "crowd_whale_divergence": bool,
                "behavior_score": float (0-10),
                "explanation": str
            }
        """
        # Извлекаем данные
        fomo = svd_data.get("fomo", False)
        panic = svd_data.get("panic", False)
        strong_fomo = svd_data.get("strong_fomo", False)
        strong_panic = svd_data.get("strong_panic", False)
        svd_intent = svd_data.get("intent", "unclear")
        phase = svd_data.get("phase", "discovery")
        cvd_divergence = svd_data.get("cvd_divergence", False)
        
        is_trap = trap_data.get("is_trap", False)
        trap_type = trap_data.get("trap_type")
        trap_score = trap_data.get("trap_score", 0)
        
        # === 1. CROWD SENTIMENT ===
        crowd_sentiment = self._determine_crowd_sentiment(fomo, panic, strong_fomo, strong_panic, is_trap)
        
        # === 2. CROWD TRAPPED ===
        crowd_trapped = is_trap and trap_score >= 3.0
        
        # === 3. WHALE ACTION ===
        whale_action = self._determine_whale_action(svd_intent, phase)
        
        # === 4. WHALE CONFIDENCE (насколько явные действия китов) ===
        whale_confidence = self._calculate_whale_confidence(svd_data, phase)
        
        # === 5. DIVERGENCE (толпа vs киты) ===
        crowd_whale_divergence = self._detect_crowd_whale_divergence(
            crowd_sentiment, whale_action, svd_intent, is_trap
        )
        
        # === 6. BEHAVIOR SCORE (общая оценка поведенческого анализа) ===
        behavior_score = self._calculate_behavior_score(
            crowd_trapped, whale_confidence, crowd_whale_divergence, cvd_divergence
        )
        
        # === 7. EXPLANATION ===
        explanation = self._generate_explanation(
            crowd_sentiment, crowd_trapped, whale_action, whale_confidence, 
            crowd_whale_divergence, trap_type
        )
        
        return {
            "crowd_sentiment": crowd_sentiment,
            "crowd_trapped": crowd_trapped,
            "whale_action": whale_action,
            "whale_confidence": whale_confidence,
            "crowd_whale_divergence": crowd_whale_divergence,
            "behavior_score": behavior_score,
            "explanation": explanation
        }
    
    def _determine_crowd_sentiment(self, fomo, panic, strong_fomo, strong_panic, is_trap):
        """Определяет эмоциональное состояние толпы"""
        if strong_fomo or (fomo and is_trap):
            return "fomo"  # Агрессивная жадность
        elif strong_panic or (panic and is_trap):
            return "panic"  # Паника
        elif fomo:
            return "greedy"  # Жадность
        elif panic:
            return "fearful"  # Страх
        else:
            return "neutral"  # Нейтрально
    
    def _determine_whale_action(self, svd_intent, phase):
        """Определяет действия китов"""
        if phase == "manipulation":
            return "manipulating"
        elif phase == "execution":
            if svd_intent == "accumulating":
                return "accumulating"
            elif svd_intent == "distributing":
                return "distributing"
            else:
                return "inactive"
        elif phase == "distribution":
            return "distributing"
        elif phase == "discovery":
            return "inactive"
        else:
            # Fallback на SVD intent
            if svd_intent in ("accumulating", "distributing"):
                return svd_intent
            return "inactive"
    
    def _calculate_whale_confidence(self, svd_data, phase):
        """Рассчитывает уверенность в действиях китов"""
        confidence = 0.0
        
        # Фаза
        if phase == "execution":
            confidence += 3.0
        elif phase == "distribution":
            confidence += 2.0
        elif phase == "manipulation":
            confidence += 1.5
        
        # Absorption
        if svd_data.get("absorption", {}).get("absorbing"):
            confidence += 1.5
        
        # Spoof confirmed
        if svd_data.get("spoof_confirmed", False):
            confidence += 1.0
        
        # CVD confirms intent
        if svd_data.get("cvd_confirms_intent", False):
            confidence += 1.5
        
        # DOM imbalance подтверждает
        dom_side = svd_data.get("dom_imbalance", {}).get("side", "neutral")
        intent = svd_data.get("intent", "unclear")
        if (dom_side == "bid" and intent == "accumulating") or \
           (dom_side == "ask" and intent == "distributing"):
            confidence += 1.0
        
        return min(confidence, 10.0)
    
    def _detect_crowd_whale_divergence(self, crowd_sentiment, whale_action, svd_intent, is_trap):
        """Детектирует расхождение между поведением толпы и китов"""
        # Толпа жадничает, киты распределяют
        if crowd_sentiment in ("greedy", "fomo") and whale_action == "distributing":
            return True
        # Толпа в панике, киты накапливают
        if crowd_sentiment in ("fearful", "panic") and whale_action == "accumulating":
            return True
        # Trap всегда означает divergence
        if is_trap:
            return True
        return False
    
    def _calculate_behavior_score(self, crowd_trapped, whale_confidence, 
                                   crowd_whale_divergence, cvd_divergence):
        """Рассчитывает общий behavior score"""
        score = 0.0
        
        # Trap - сильный сигнал
        if crowd_trapped:
            score += 3.0
        
        # Whale confidence
        score += whale_confidence * 0.4
        
        # Divergence
        if crowd_whale_divergence:
            score += 2.0
        if cvd_divergence:
            score += 1.0
        
        return min(score, 10.0)
    
    def _generate_explanation(self, crowd_sentiment, crowd_trapped, whale_action, 
                              whale_confidence, crowd_whale_divergence, trap_type):
        """Генерирует объяснение на русском"""
        parts = []
        
        # Толпа
        sentiment_map = {
            "fomo": "толпа в FOMO (агрессивная жадность)",
            "panic": "толпа в панике",
            "greedy": "толпа жадничает",
            "fearful": "толпа в страхе",
            "neutral": "толпа нейтральна"
        }
        parts.append(f"Толпа: {sentiment_map.get(crowd_sentiment, 'neutral')}")
        
        # Киты
        whale_map = {
            "accumulating": "киты накапливают позиции",
            "distributing": "киты распределяют позиции",
            "manipulating": "киты манипулируют рынком",
            "inactive": "киты неактивны"
        }
        parts.append(f"Киты: {whale_map.get(whale_action, 'inactive')} (уверенность: {whale_confidence:.1f}/10)")
        
        # Trap
        if crowd_trapped:
            if trap_type == "bull_trap":
                parts.append("⚠️ ЛОВУШКА ДЛЯ ПОКУПАТЕЛЕЙ (bull trap)")
            elif trap_type == "bear_trap":
                parts.append("⚠️ ЛОВУШКА ДЛЯ ПРОДАВЦОВ (bear trap)")
        
        # Divergence
        if crowd_whale_divergence:
            parts.append("❗ Толпа и киты действуют в противоположных направлениях")
        
        return ". ".join(parts)

