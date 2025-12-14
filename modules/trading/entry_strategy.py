# modules/trading/entry_strategy.py

"""
Стратегия входа в позицию
Логика: вход от нижней границы коридора при тренде вверх
"""

import logging

logger = logging.getLogger(__name__)


class EntryStrategy:
    """
    Определяет точки входа в позицию на основе:
    - Глобального тренда
    - Фазы накопления
    - Бокового коридора
    - Позиции цены в коридоре
    """
    
    def __init__(self):
        pass
    
    def calculate_entry_signal(self, global_trend, accumulation_phase, range_data, current_price):
        """
        Рассчитывает сигнал входа
        
        Args:
            global_trend: данные глобального тренда {
                "global_direction": "up" | "down" | "neutral",
                "global_trend_strength": 0.0-1.0,
                "consensus": "strong_up" | "up" | "neutral" | "down" | "strong_down"
            }
            accumulation_phase: данные фазы накопления {
                "current_phase": "accumulation" | "distribution" | "neutral",
                "global_trend": "accumulation" | "distribution" | "neutral"
            }
            range_data: данные коридора от RangeDetector
            current_price: текущая цена
        
        Returns:
            dict: {
                "entry_signal": "BUY" | "SELL" | "WAIT",
                "entry_price": float,  # Цена входа
                "entry_reason": str,  # Причина входа
                "entry_confidence": 0.0-1.0,  # Уверенность во входе
                "stop_loss": float,  # Стоп-лосс
                "take_profit": float,  # Тейк-профит
                "risk_reward_ratio": float  # Соотношение риск/прибыль
            }
        """
        # Условие 1: Должен быть боковой коридор
        if not range_data.get("is_range", False):
            return {
                "entry_signal": "WAIT",
                "entry_price": current_price,
                "entry_reason": "Нет бокового коридора",
                "entry_confidence": 0.0,
                "stop_loss": current_price,
                "take_profit": current_price,
                "risk_reward_ratio": 0.0
            }
        
        # Условие 2: Должна быть фаза накопления
        is_accumulation = (
            accumulation_phase.get("current_phase") == "accumulation" or
            accumulation_phase.get("global_trend") == "accumulation"
        )
        
        if not is_accumulation:
            return {
                "entry_signal": "WAIT",
                "entry_price": current_price,
                "entry_reason": "Не фаза накопления",
                "entry_confidence": 0.0,
                "stop_loss": current_price,
                "take_profit": current_price,
                "risk_reward_ratio": 0.0
            }
        
        # Условие 3: Глобальный тренд должен быть определён
        global_direction = global_trend.get("global_direction", "neutral")
        global_strength = global_trend.get("global_trend_strength", 0.0)
        consensus = global_trend.get("consensus", "neutral")
        
        # ЛОГИКА: Вход от нижней границы если тренд ВВЕРХ
        range_low = range_data.get("range_low", current_price)
        range_high = range_data.get("range_high", current_price)
        current_position = range_data.get("current_position", "middle")
        distance_to_low_pct = range_data.get("distance_to_low_pct", 0.0)
        range_quality = range_data.get("range_quality", 0.0)
        
        # СЛУЧАЙ 1: Тренд ВВЕРХ → BUY от нижней границы
        if global_direction == "up" and global_strength > 0.5:
            # Вход когда цена близко к нижней границе
            entry_threshold_pct = 1.0  # Вход если цена в пределах 1% от нижней границы
            
            if distance_to_low_pct <= entry_threshold_pct:
                # Рассчитываем уровни
                entry_price = range_low * 1.001  # Немного выше нижней границы (0.1%)
                stop_loss = range_low * 0.995  # Стоп ниже нижней границы (0.5%)
                take_profit = range_high * 1.002  # Тейк-профит у верхней границы (0.2% выше)
                
                # Risk/Reward
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
                risk_reward_ratio = reward / risk if risk > 0 else 0.0
                
                # Confidence зависит от:
                # - Силы глобального тренда
                # - Качества коридора
                # - Консенсуса таймфреймов
                confidence = (
                    global_strength * 0.4 +  # 40% - сила тренда
                    range_quality * 0.3 +    # 30% - качество коридора
                    (0.5 if consensus in ("strong_up", "up") else 0.2) * 0.3  # 30% - консенсус
                )
                
                reason = f"BUY от нижней границы коридора: тренд {global_direction.upper()} " \
                        f"(сила: {global_strength:.0%}), фаза накопления, " \
                        f"цена в {current_position} коридора (расстояние до низа: {distance_to_low_pct:.2f}%)"
                
                logger.info(f"✅ ENTRY SIGNAL: BUY от ${range_low:.2f} "
                           f"(confidence: {confidence:.2f}, R/R: {risk_reward_ratio:.2f})")
                
                return {
                    "entry_signal": "BUY",
                    "entry_price": entry_price,
                    "entry_reason": reason,
                    "entry_confidence": confidence,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "risk_reward_ratio": risk_reward_ratio
                }
            else:
                # Цена ещё не у нижней границы - ждём
                return {
                    "entry_signal": "WAIT",
                    "entry_price": current_price,
                    "entry_reason": f"Ждём приближения к нижней границе (сейчас: {distance_to_low_pct:.2f}% от низа)",
                    "entry_confidence": 0.0,
                    "stop_loss": current_price,
                    "take_profit": current_price,
                    "risk_reward_ratio": 0.0
                }
        
        # СЛУЧАЙ 2: Тренд ВНИЗ → SELL от верхней границы
        elif global_direction == "down" and global_strength > 0.5:
            distance_to_high_pct = range_data.get("distance_to_high_pct", 0.0)
            entry_threshold_pct = 1.0
            
            if distance_to_high_pct <= entry_threshold_pct:
                # Рассчитываем уровни
                entry_price = range_high * 0.999  # Немного ниже верхней границы
                stop_loss = range_high * 1.005  # Стоп выше верхней границы
                take_profit = range_low * 0.998  # Тейк-профит у нижней границы
                
                # Risk/Reward
                risk = stop_loss - entry_price
                reward = entry_price - take_profit
                risk_reward_ratio = reward / risk if risk > 0 else 0.0
                
                confidence = (
                    global_strength * 0.4 +
                    range_quality * 0.3 +
                    (0.5 if consensus in ("strong_down", "down") else 0.2) * 0.3
                )
                
                reason = f"SELL от верхней границы коридора: тренд {global_direction.upper()} " \
                        f"(сила: {global_strength:.0%}), фаза накопления, " \
                        f"цена в {current_position} коридора (расстояние до верха: {distance_to_high_pct:.2f}%)"
                
                logger.info(f"✅ ENTRY SIGNAL: SELL от ${range_high:.2f} "
                           f"(confidence: {confidence:.2f}, R/R: {risk_reward_ratio:.2f})")
                
                return {
                    "entry_signal": "SELL",
                    "entry_price": entry_price,
                    "entry_reason": reason,
                    "entry_confidence": confidence,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "risk_reward_ratio": risk_reward_ratio
                }
            else:
                return {
                    "entry_signal": "WAIT",
                    "entry_price": current_price,
                    "entry_reason": f"Ждём приближения к верхней границе (сейчас: {distance_to_high_pct:.2f}% от верха)",
                    "entry_confidence": 0.0,
                    "stop_loss": current_price,
                    "take_profit": current_price,
                    "risk_reward_ratio": 0.0
                }
        
        # СЛУЧАЙ 3: Нейтральный тренд или слабый
        else:
            return {
                "entry_signal": "WAIT",
                "entry_price": current_price,
                "entry_reason": f"Тренд {global_direction} слишком слабый (сила: {global_strength:.0%}) или нейтральный",
                "entry_confidence": 0.0,
                "stop_loss": current_price,
                "take_profit": current_price,
                "risk_reward_ratio": 0.0
            }

