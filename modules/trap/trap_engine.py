# modules/trap/trap_engine.py

"""
Trap Engine - детекция ловушек для толпы
Определяет момент когда толпа попала в ловушку и киты готовы развернуть цену
"""

import logging

logger = logging.getLogger(__name__)


class TrapEngine:
    """
    Детектирует ловушки (traps) для толпы
    """
    
    def __init__(self, config=None):
        self.config = config
        self.trap_score_threshold = getattr(config, 'TRAP_SCORE_THRESHOLD', 3.0) if config else 3.0
    
    def analyze(self, svd_data, liquidity_data, market_structure, ta_data, current_price=None):
        """
        Анализирует все данные для детекции trap-сценариев
        
        Args:
            svd_data: данные от SVDEngine
            liquidity_data: данные от LiquidityEngine
            market_structure: данные от MarketStructureEngine
            ta_data: данные от TAEngine
            current_price: текущая цена
            
        Returns:
            dict: {
                "is_trap": bool,
                "trap_type": "bull_trap" | "bear_trap" | None,
                "trap_score": float (0-10),
                "trap_reasons": [list of reasons],
                "expected_reversal_direction": "up" | "down" | None
            }
        """
        trap_score = 0.0
        trap_reasons = []
        trap_type = None
        expected_reversal = None
        
        # Извлекаем данные
        svd_intent = svd_data.get("intent", "unclear")
        liq_dir = liquidity_data.get("direction", {}).get("direction", "neutral")
        fomo = svd_data.get("fomo", False)
        panic = svd_data.get("panic", False)
        strong_fomo = svd_data.get("strong_fomo", False)
        strong_panic = svd_data.get("strong_panic", False)
        cvd_divergence = svd_data.get("cvd_divergence", False)
        cvd_slope = svd_data.get("cvd_slope", 0)
        absorption = svd_data.get("absorption", {})
        dom_imbalance = svd_data.get("dom_imbalance", {})
        thin_zones = svd_data.get("thin_zones", {})
        spoof_wall = svd_data.get("spoof_wall", {})
        spoof_confirmed = svd_data.get("spoof_confirmed", False)
        sweeps = liquidity_data.get("sweeps", {})
        phase = svd_data.get("phase", "discovery")
        
        # === BULL TRAP DETECTION (толпа покупает, киты готовят дамп) ===
        
        # 1. FOMO + distributing intent
        if (fomo or strong_fomo) and svd_intent == "distributing":
            trap_score += 2.0
            trap_reasons.append("Толпа в FOMO, но киты распределяют позиции")
            trap_type = "bull_trap"
            expected_reversal = "down"
        
        # 2. Ликвидность вверх + CVD дивергенция (цена вверх, CVD вниз)
        if liq_dir == "up" and cvd_divergence and cvd_slope < 0:
            trap_score += 1.5
            trap_reasons.append("Ликвидность вверх, но CVD показывает слабость покупок (дивергенция)")
            trap_type = "bull_trap"
            expected_reversal = "down"
        
        # 3. Спуф на поддержку исчез + absorption на селл
        if spoof_confirmed and spoof_wall.get("side") == "bid" and absorption.get("absorbing") and absorption.get("side") == "sell":
            trap_score += 1.5
            trap_reasons.append("Фейковая поддержка (bid spoof) исчезла, началось поглощение на продажу")
            trap_type = "bull_trap"
            expected_reversal = "down"
        
        # 4. DOM дисбаланс в ask (продавцы), но цена еще растёт (фаза distribution)
        if phase == "distribution" and dom_imbalance.get("side") == "ask" and liq_dir == "up":
            trap_score += 1.0
            trap_reasons.append("Фаза distribution: киты продают, но цена еще держится")
            trap_type = "bull_trap"
            expected_reversal = "down"
        
        # 5. Sweep вверх + тонкая ликвидность снизу (легко упадёт)
        if sweeps.get("sweep_up") and thin_zones.get("thin_below"):
            trap_score += 1.0
            trap_reasons.append("Свип вверх собрал стопы, снизу тонкая ликвидность — лёгкий путь вниз")
            trap_type = "bull_trap"
            expected_reversal = "down"
        
        # === BEAR TRAP DETECTION (толпа продаёт, киты готовят pump) ===
        
        # 1. Panic + accumulating intent
        if (panic or strong_panic) and svd_intent == "accumulating":
            trap_score += 2.0
            trap_reasons.append("Толпа в панике, но киты накапливают позиции")
            trap_type = "bear_trap"
            expected_reversal = "up"
        
        # 2. Ликвидность вниз + CVD дивергенция (цена вниз, CVD вверх)
        if liq_dir == "down" and cvd_divergence and cvd_slope > 0:
            trap_score += 1.5
            trap_reasons.append("Ликвидность вниз, но CVD показывает силу покупок (дивергенция)")
            trap_type = "bear_trap"
            expected_reversal = "up"
        
        # 3. Спуф на сопротивление исчез + absorption на buy
        if spoof_confirmed and spoof_wall.get("side") == "ask" and absorption.get("absorbing") and absorption.get("side") == "buy":
            trap_score += 1.5
            trap_reasons.append("Фейковое сопротивление (ask spoof) исчезло, началось поглощение на покупку")
            trap_type = "bear_trap"
            expected_reversal = "up"
        
        # 4. DOM дисбаланс в bid (покупатели), но цена еще падает (фаза accumulation скрытая)
        if phase in ("discovery", "manipulation") and dom_imbalance.get("side") == "bid" and liq_dir == "down":
            trap_score += 1.0
            trap_reasons.append("Киты покупают, но цена еще падает — скрытое накопление")
            trap_type = "bear_trap"
            expected_reversal = "up"
        
        # 5. Sweep вниз + тонкая ликвидность сверху (легко вырастет)
        if sweeps.get("sweep_down") and thin_zones.get("thin_above"):
            trap_score += 1.0
            trap_reasons.append("Свип вниз собрал стопы, сверху тонкая ликвидность — лёгкий путь вверх")
            trap_type = "bear_trap"
            expected_reversal = "up"
        
        # Определяем is_trap
        is_trap = trap_score >= self.trap_score_threshold
        
        if is_trap:
            logger.warning(f"🪤 TRAP ОБНАРУЖЕН: {trap_type} (score: {trap_score:.1f}/10)")
            logger.warning(f"   Причины: {', '.join(trap_reasons[:3])}")
        
        return {
            "is_trap": is_trap,
            "trap_type": trap_type,
            "trap_score": min(trap_score, 10.0),
            "trap_reasons": trap_reasons,
            "expected_reversal_direction": expected_reversal
        }
    
    def get_trap_signal_adjustment(self, trap_result, current_signal):
        """
        Возвращает корректировку сигнала на основе trap detection
        
        Args:
            trap_result: результат analyze()
            current_signal: текущий сигнал ("BUY", "SELL", "WAIT")
            
        Returns:
            dict: {
                "adjusted_signal": str,
                "confidence_adjustment": float,
                "reason": str
            }
        """
        if not trap_result["is_trap"]:
            return {
                "adjusted_signal": current_signal,
                "confidence_adjustment": 0.0,
                "reason": "Trap не обнаружен"
            }
        
        trap_type = trap_result["trap_type"]
        trap_score = trap_result["trap_score"]
        
        # Bull trap: сигнал BUY опасен, разворачиваем в SELL или WAIT
        if trap_type == "bull_trap":
            if current_signal == "BUY":
                # Если trap score высокий — разворачиваем сигнал
                if trap_score >= 5.0:
                    return {
                        "adjusted_signal": "SELL",
                        "confidence_adjustment": -3.0,
                        "reason": f"Bull trap (score: {trap_score:.1f}) — разворот сигнала BUY→SELL"
                    }
                else:
                    return {
                        "adjusted_signal": "WAIT",
                        "confidence_adjustment": -5.0,
                        "reason": f"Bull trap (score: {trap_score:.1f}) — блокировка BUY"
                    }
            elif current_signal == "SELL":
                # SELL подтверждается trap
                return {
                    "adjusted_signal": "SELL",
                    "confidence_adjustment": +1.5,
                    "reason": f"Bull trap подтверждает SELL (score: {trap_score:.1f})"
                }
        
        # Bear trap: сигнал SELL опасен, разворачиваем в BUY или WAIT
        elif trap_type == "bear_trap":
            if current_signal == "SELL":
                # Если trap score высокий — разворачиваем сигнал
                if trap_score >= 5.0:
                    return {
                        "adjusted_signal": "BUY",
                        "confidence_adjustment": -3.0,
                        "reason": f"Bear trap (score: {trap_score:.1f}) — разворот сигнала SELL→BUY"
                    }
                else:
                    return {
                        "adjusted_signal": "WAIT",
                        "confidence_adjustment": -5.0,
                        "reason": f"Bear trap (score: {trap_score:.1f}) — блокировка SELL"
                    }
            elif current_signal == "BUY":
                # BUY подтверждается trap
                return {
                    "adjusted_signal": "BUY",
                    "confidence_adjustment": +1.5,
                    "reason": f"Bear trap подтверждает BUY (score: {trap_score:.1f})"
                }
        
        return {
            "adjusted_signal": current_signal,
            "confidence_adjustment": 0.0,
            "reason": "Trap не влияет на текущий сигнал"
        }

