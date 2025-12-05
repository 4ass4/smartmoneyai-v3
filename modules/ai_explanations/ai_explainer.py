# modules/ai_explanations/ai_explainer.py

from .text_templates import get_template, format_explanation


class AIExplainer:
    """
    Генератор объяснений на русском языке
    Преобразует технические данные в понятные тексты
    """

    def __init__(self):
        pass

    def explain_liquidity(self, liquidity_data):
        """Объясняет данные ликвидности"""
        direction = liquidity_data.get("direction", {}).get("direction", "neutral")
        reason = liquidity_data.get("direction", {}).get("reason", "")
        
        if direction == "up":
            return f"Цена с высокой вероятностью пойдёт вверх. {reason}"
        elif direction == "down":
            return f"Цена с высокой вероятностью пойдёт вниз. {reason}"
        else:
            return "Направление движения не определено."
    
    def explain_svd(self, svd_data):
        """Объясняет данные SVD"""
        intent = svd_data.get("intent", "unclear")
        delta = svd_data.get("delta", 0)
        absorption = svd_data.get("absorption", {})
        
        parts = []
        
        if intent == "accumulating":
            parts.append("Крупные игроки накапливают позиции")
        elif intent == "distributing":
            parts.append("Крупные игроки распределяют позиции")
        
        if absorption.get("absorbing"):
            side = absorption.get("side", "")
            parts.append(f"обнаружено поглощение со стороны {side}")
        
        if abs(delta) > 100000:
            if delta > 0:
                parts.append("сильное преобладание покупок")
            else:
                parts.append("сильное преобладание продаж")
        
        return ". ".join(parts) if parts else "Активность крупных игроков неясна."
    
    def explain_structure(self, structure_data):
        """Объясняет структуру рынка"""
        trend = structure_data.get("trend", "range")
        range_info = structure_data.get("range", {})
        
        if trend == "bullish":
            return "Рынок в бычьем тренде. Структура показывает рост."
        elif trend == "bearish":
            return "Рынок в медвежьем тренде. Структура показывает падение."
        elif range_info.get("in_range"):
            return f"Рынок в боковом диапазоне между {range_info.get('bottom')} и {range_info.get('top')}"
        else:
            return "Структура рынка неопределенная."
    
    def explain_decision(self, decision_data):
        """Генерирует полное объяснение решения"""
        signal = decision_data.get("signal", "WAIT")
        confidence = decision_data.get("confidence", 0)
        explanation = decision_data.get("explanation", "")
        
        template = get_template("decision")
        return format_explanation(template, {
            "signal": signal,
            "confidence": confidence,
            "explanation": explanation
        })

