# bot/formatting/signal_formatter.py

from modules.ai_explanations.russian_explainer import RussianExplainer


def format_signal(signal_data, structure_data=None, liquidity_data=None, svd_data=None, ta_data=None, current_price=None):
    """
    Форматирование сигнала для отправки в Telegram с детальными объяснениями
    
    Args:
        signal_data: данные сигнала
        structure_data: данные структуры рынка (опционально)
        liquidity_data: данные ликвидности (опционально)
        svd_data: данные SVD (опционально)
        ta_data: данные TA (опционально)
        current_price: текущая цена (опционально)
        
    Returns:
        Отформатированная строка
    """
    signal = signal_data.get("signal", "WAIT")
    confidence = signal_data.get("confidence", 0)
    
    # Эмодзи для сигналов
    emoji_map = {
        "BUY": "🟢",
        "SELL": "🔴",
        "WAIT": "🟡"
    }
    
    emoji = emoji_map.get(signal, "⚪")
    
    # Определяем уровень уверенности
    if confidence >= 7.0:
        confidence_level = "🔥 HIGH"
    elif confidence >= 5.5:
        confidence_level = "✅ MEDIUM"
    elif confidence >= 4.0:
        confidence_level = "⚠️ LOW"
    else:
        confidence_level = "❌ VERY LOW"
    
    # Если есть все данные - используем детальный формат
    if all([structure_data, liquidity_data, svd_data, ta_data, current_price]):
        # Генерируем детальное объяснение
        detailed_explanation = RussianExplainer.generate_detailed_explanation(
            signal_data, structure_data, liquidity_data, svd_data, ta_data, current_price
        )
        
        # Проверяем на противоречия
        svd_intent = svd_data.get('intent', 'unclear')
        warning = ""
        if signal == "BUY" and svd_intent == "distributing":
            warning = "\n\n⚠️ ВНИМАНИЕ: Противоречие - SVD показывает распределение, но сигнал BUY"
        elif signal == "SELL" and svd_intent == "accumulating":
            warning = "\n\n⚠️ ВНИМАНИЕ: Противоречие - SVD показывает накопление, но сигнал SELL"
        
        message = f"""
📊 <b>АВТОМАТИЧЕСКИЙ СИГНАЛ</b>

💰 Цена: ${current_price:,.2f}

{emoji} <b>СИГНАЛ: {signal}</b>
📈 Уверенность: {confidence:.1f}/10 ({confidence_level})
{warning}

{detailed_explanation}
        """
    else:
        # Упрощенный формат если нет всех данных
        explanation = signal_data.get("explanation", "")
        message = f"""
{emoji} <b>СИГНАЛ: {signal}</b>
📊 Уверенность: {confidence:.1f}/10 ({confidence_level})

📝 {explanation}
        """
    
    # Добавляем уровни, если есть реальные значения
    levels = signal_data.get("levels", {})
    if levels:
        levels_parts = []
        
        if "entry_zone" in levels and levels["entry_zone"]:
            entry = levels["entry_zone"]
            if entry and entry != "определяется по структуре рынка":
                levels_parts.append(f"Вход: {entry}")
        
        if "targets" in levels and levels["targets"]:
            targets = [t for t in levels["targets"] if t and t != "target_1" and t != "target_2"]
            if targets:
                levels_parts.append(f"Цели: {', '.join(str(t) for t in targets)}")
        
        if "invalidation" in levels and levels["invalidation"]:
            invalidation = levels["invalidation"]
            if invalidation and invalidation != "уровень инвалидации":
                levels_parts.append(f"Стоп: {invalidation}")
        
        if levels_parts:
            message += "\n\n📍 <b>Уровни:</b>"
            for part in levels_parts:
                message += f"\n   • {part}"
    
    return message.strip()

