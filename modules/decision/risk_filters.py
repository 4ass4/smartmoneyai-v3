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
    
    # Проверка на критический конфликт сигналов
    # (теперь более мягкая - только если все сигналы противоречат)
    liq_dir = signals["liquidity"].get("direction", {}).get("direction", "neutral")
    svd_intent = signals["svd"].get("intent", "unclear")
    trend = signals["structure"].get("trend", "range")
    signal_type = signals.get("signal", "WAIT")
    
    # Критические противоречия (блокируем только при полном конфликте)
    critical_conflicts = 0
    
    # Противоречие: сигнал BUY, но SVD distributing
    if signal_type == "BUY" and svd_intent == "distributing":
        critical_conflicts += 1
    
    # Противоречие: сигнал SELL, но SVD accumulating
    if signal_type == "SELL" and svd_intent == "accumulating":
        critical_conflicts += 1
    
    # Противоречие: сигнал BUY, но ликвидность вниз
    if signal_type == "BUY" and liq_dir == "down":
        critical_conflicts += 1
    
    # Противоречие: сигнал SELL, но ликвидность вверх
    if signal_type == "SELL" and liq_dir == "up":
        critical_conflicts += 1
    
    # Блокируем только если 2+ критических противоречия ИЛИ все 3 основных сигнала противоречат
    if critical_conflicts >= 2:
        return {
            "allowed": False,
            "reason": f"Критические противоречия между сигналами ({critical_conflicts} конфликтов)"
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

