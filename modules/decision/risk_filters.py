# modules/decision/risk_filters.py


def apply_risk_filters(signals, confidence):
    """
    Применяет фильтры риска к сигналу
    
    Args:
        signals: словарь со всеми сигналами
        confidence: уровень уверенности (0-10)
        
    Returns:
        Dict с результатом фильтрации
    """
    # Минимальный confidence (снижен порог для тестирования)
    # Можно снизить до 2.0 для более частых сигналов
    MIN_CONFIDENCE = 2.0
    if confidence < MIN_CONFIDENCE:
        return {
            "allowed": False,
            "reason": f"Слишком низкая уверенность сигнала ({confidence:.1f} < {MIN_CONFIDENCE})"
        }
    
    # Проверка на конфликт сигналов
    liq_dir = signals["liquidity"].get("direction", {}).get("direction", "neutral")
    svd_intent = signals["svd"].get("intent", "unclear")
    trend = signals["structure"].get("trend", "range")
    
    # Если все сигналы противоречат друг другу
    conflicts = 0
    if liq_dir == "up" and trend == "bearish":
        conflicts += 1
    if liq_dir == "down" and trend == "bullish":
        conflicts += 1
    if svd_intent == "accumulating" and trend == "bearish":
        conflicts += 1
    if svd_intent == "distributing" and trend == "bullish":
        conflicts += 1
    
    if conflicts >= 2:
        return {
            "allowed": False,
            "reason": "Слишком много конфликтов между сигналами"
        }
    
    # Проверка на перекупленность/перепроданность
    ta_data = signals.get("ta", {})
    if ta_data.get("overbought") and signals.get("signal") == "BUY":
        return {
            "allowed": False,
            "reason": "Рынок перекуплен, не рекомендуется покупка"
        }
    
    if ta_data.get("oversold") and signals.get("signal") == "SELL":
        return {
            "allowed": False,
            "reason": "Рынок перепродан, не рекомендуется продажа"
        }
    
    return {
        "allowed": True,
        "reason": "Сигнал прошел все фильтры"
    }

