# modules/svd/velocity.py

def detect_trade_velocity(trades):
    """
    Скорость сделок — важный показатель:
    - быстрое исполнение = паника/сквиз/агрессивная закупка.
    - низкая скорость = фаза накопления/ожидания.
    """
    if not trades or not isinstance(trades, list) or len(trades) < 2:
        return {"velocity": 0}

    try:
        times = [float(t.get("timestamp", 0)) for t in trades if isinstance(t, dict)]
        if len(times) < 2:
            return {"velocity": 0}
        
        total_time = times[-1] - times[0]
        if total_time == 0:
            return {"velocity": len(trades)}

        velocity = len(trades) / (total_time / 1000)  # Конвертируем в секунды
        return {"velocity": velocity}
    except (KeyError, ValueError, TypeError, IndexError):
        return {"velocity": 0}

