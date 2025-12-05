# modules/ai_explanations/text_templates.py


def get_template(template_name):
    """
    Возвращает шаблон текста по имени
    
    Args:
        template_name: имя шаблона
        
    Returns:
        Строка шаблона
    """
    templates = {
        "decision": """
🎯 СИГНАЛ: {signal}
📊 Уверенность: {confidence}/10

📝 Объяснение:
{explanation}
        """,
        "liquidity": "Ликвидность указывает на движение: {direction}",
        "svd": "Анализ потока ордеров: {intent}",
        "structure": "Структура рынка: {trend}"
    }
    
    return templates.get(template_name, "{explanation}")


def format_explanation(template, data):
    """
    Форматирует шаблон с данными
    
    Args:
        template: строка шаблона
        data: словарь с данными
        
    Returns:
        Отформатированная строка
    """
    try:
        return template.format(**data)
    except KeyError:
        # Если не хватает данных, возвращаем как есть
        return template

