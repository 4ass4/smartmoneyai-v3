# modules/decision/decision_engine.py

from .risk_filters import apply_risk_filters
from .conflict_detector import ConflictDetector
from modules.trap.trap_engine import TrapEngine
from modules.behavior.behavior_engine import BehaviorEngine


class DecisionEngine:
    """
    Decision Engine v3.0
    Финальный блок, объединяющий все модули и принимающий решение
    """

    def __init__(self, config=None):
        self.config = config
        self.min_confidence = 7.0 if config is None else getattr(config, 'MIN_CONFIDENCE', 7.0)
        self.conflict_detector = ConflictDetector(config)
        self.trap_engine = TrapEngine(config)
        self.behavior_engine = BehaviorEngine(config)

    def analyze(self, liquidity_data, svd_data, market_structure, ta_data, current_price=None, htf_context=None, htf_liquidity=None, data_quality=None):
        """
        Главный метод принятия решения
        
        Args:
            liquidity_data: данные от LiquidityEngine
            svd_data: данные от SVDEngine
            market_structure: данные от MarketStructureEngine
            ta_data: данные от TAEngine
            current_price: текущая цена (опционально)
            data_quality: результат валидации данных (опционально)
            
        Returns:
            Dict с финальным сигналом и объяснением
        """
        # Сбор всех сигналов
        signals = {
            "liquidity": liquidity_data,
            "svd": svd_data,
            "structure": market_structure,
            "ta": ta_data,
            "current_price": current_price,
            "htf": htf_context or {},
            "htf_liq": htf_liquidity or {},
            "data_quality": data_quality or {"overall_quality": 1.0}
        }
        
        # Определение направления
        direction = self._determine_direction(signals)
        signals["signal"] = direction
        
        # Расчет confidence
        confidence = self._calculate_confidence(signals)
        
        # Детекция конфликтов
        conflict_result = self.conflict_detector.detect_conflicts(signals)
        signals["conflicts"] = conflict_result
        
        # КРИТИЧНО: Проверяем trap СРАЗУ ПОСЛЕ конфликтов
        # Чтобы не блокировать TRAP сигналы из-за "конфликтов"
        # Trap Detection - ловушки для толпы
        trap_result = self.trap_engine.analyze(
            signals["svd"],
            signals["liquidity"],
            signals["structure"],
            signals["ta"],
            current_price
        )
        signals["trap"] = trap_result
        
        # Проверка критичных конфликтов
        # НО! Если обнаружен сильный TRAP → конфликты это ПРИЗНАК манипуляции!
        should_wait, conflict_reason = self.conflict_detector.should_force_wait(conflict_result)
        
        # Если обнаружен TRAP с высоким score → НЕ блокируем сигнал из-за конфликтов
        is_strong_trap = trap_result.get("is_trap") and trap_result.get("trap_score", 0) >= 4.0
        
        if should_wait and not is_strong_trap:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"🚫 Сигнал {direction} заблокирован из-за критичных конфликтов")
            return {
                "signal": "WAIT",
                "confidence": 0,
                "reason": conflict_reason,
                "explanation": conflict_reason,
                "conflicts": conflict_result
            }
        
        # Дополнительный штраф confidence за major конфликты
        # НО! Если обнаружен TRAP → конфликты это ПРИЗНАК TRAP, не штрафуем!
        if conflict_result["severity"] == "major":
            # Если обнаружен сильный TRAP (score >= 4.0) → НЕ штрафуем
            if is_strong_trap:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"🎭 TRAP DETECTED: конфликты это ПРИЗНАК манипуляции, НЕ штрафуем confidence")
                logger.info(f"   🎭 Trap type: {trap_result.get('trap_type')}, score: {trap_result.get('trap_score'):.1f}")
                # Наоборот УСИЛИВАЕМ confidence за обнаружение TRAP
                trap_bonus = trap_result.get("trap_score", 0) * 0.5  # 50% от trap_score
                confidence += trap_bonus
                logger.info(f"   📈 Бонус за TRAP detection: +{trap_bonus:.1f}")
            else:
                # Обычный штраф за конфликты (если НЕ trap)
                conflict_penalty = min(2.0, conflict_result["conflict_count"] * 0.5)
                confidence -= conflict_penalty
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"   📉 Штраф за конфликты: -{conflict_penalty:.1f} (severity: major)")
        
        # Опциональный фильтр: только фаза execution (меньше шумов, выше "уверенность" в смысле действия китов)
        svd_phase = signals["svd"].get("phase", "discovery")
        if getattr(self.config, "EXECUTION_ONLY_SIGNALS", False):
            if svd_phase != "execution" and confidence < 6:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Фильтр EXECUTION_ONLY: фаза {svd_phase}, confidence {confidence:.1f} < 6 — возвращаем WAIT")
                return {
                    "signal": "WAIT",
                    "confidence": 0,
                    "reason": "Ожидаем фазу execution для подтверждения действий крупных игроков",
                    "explanation": "Недостаточно признаков фазы execution, сигнал пропущен",
                    "conflicts": conflict_result
                }

        # Применение фильтров риска
        filtered = apply_risk_filters(signals, confidence)
        
        if not filtered["allowed"]:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"🚫 Сигнал {direction} заблокирован фильтром риска: {filtered['reason']} (confidence: {confidence:.1f}/10)")
            return {
                "signal": "WAIT",
                "confidence": 0,
                "reason": filtered["reason"],
                "explanation": filtered["reason"]
            }
        
        # trap_result уже рассчитан выше (до проверки конфликтов)
        # signals["trap"] уже установлен
        
        # Behavior Analysis - поведение толпы vs китов
        behavior_result = self.behavior_engine.analyze(
            signals["svd"],
            trap_result,
            signals["liquidity"]
        )
        signals["behavior"] = behavior_result
        
        # Применяем корректировку сигнала на основе trap detection
        trap_adjustment = self.trap_engine.get_trap_signal_adjustment(trap_result, direction)
        if trap_adjustment["adjusted_signal"] != direction:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"🪤 Trap Engine: {trap_adjustment['reason']}")
            direction = trap_adjustment["adjusted_signal"]
        
        # Корректируем confidence на основе trap
        confidence += trap_adjustment["confidence_adjustment"]
        
        # Дополнительная корректировка confidence на основе behavior
        if behavior_result["crowd_trapped"]:
            confidence += 0.5  # Trap усиливает уверенность в развороте
        if behavior_result["crowd_whale_divergence"] and not behavior_result["crowd_trapped"]:
            confidence -= 0.3  # Divergence без trap — предупреждающий сигнал
        
        confidence = min(max(confidence, 0), 10)
        
        # ПРИНУДИТЕЛЬНЫЙ WAIT для низкой уверенности
        # Если уверенность < 4.0 → слишком неопределенно для торговли
        # Синхронизировано с risk_filters.py (MIN_CONFIDENCE = 4.0)
        # АГРЕССИВНАЯ настройка для максимального количества сигналов
        MIN_CONFIDENCE_TO_TRADE = 4.0  # Снижен с 5.5 для МАКСИМАЛЬНОГО количества сигналов
        if confidence < MIN_CONFIDENCE_TO_TRADE and direction != "WAIT":
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️ VERY LOW CONFIDENCE: {confidence:.1f}/10 < {MIN_CONFIDENCE_TO_TRADE} "
                         f"→ принудительно WAIT вместо {direction}")
            direction = "WAIT"
        
        # Логирование уровня сигнала
        if direction != "WAIT":
            import logging
            logger = logging.getLogger(__name__)
            if confidence >= 7.0:
                logger.info(f"🔥 HIGH CONFIDENCE SIGNAL: {direction} ({confidence:.1f}/10)")
            elif confidence >= 5.5:
                logger.info(f"✅ MEDIUM CONFIDENCE SIGNAL: {direction} ({confidence:.1f}/10)")
            elif confidence >= 4.0:
                logger.info(f"⚠️ LOW CONFIDENCE SIGNAL: {direction} ({confidence:.1f}/10) - рискованный!")
        
        # Генерация объяснения
        explanation = self._generate_explanation(signals, direction, confidence)
        
        # Добавляем current_price в signals для расчета уровней
        if current_price is not None:
            signals["current_price"] = current_price
        
        # Определение уровней
        levels = self._calculate_levels(signals)
        
        return {
            "signal": direction,
            "confidence": confidence,
            "explanation": explanation,
            "scenario": {
                "main": explanation,
                "alternative": self._generate_alternative_scenario(signals)
            },
            "levels": levels,
            "conflicts": conflict_result,
            "trap": trap_result,
            "behavior": behavior_result
        }
    
    def _determine_direction(self, signals):
        """Определяет финальное направление на основе всех сигналов с учетом весов"""
        votes = {"BUY": 0, "SELL": 0, "WAIT": 0}
        
        # SVD Intent (вес 3.0 - САМЫЙ ВАЖНЫЙ! Показывает что делают киты СЕЙЧАС)
        svd_intent = signals["svd"].get("intent", "unclear")
        svd_conf = signals["svd"].get("confidence", 0)
        cvd_confirms = signals["svd"].get("cvd_confirms_intent", False)
        
        # Усиленный вес если CVD подтверждает intent
        svd_weight = 3.0 if cvd_confirms else 2.5
        
        if svd_intent == "accumulating" and svd_conf > 0:
            votes["BUY"] += svd_weight
        elif svd_intent == "distributing" and svd_conf > 0:
            votes["SELL"] += svd_weight
        elif svd_intent == "unclear":
            # Если SVD unclear, не добавляем голоса, но и не блокируем
            pass
        
        # Liquidity (вес 2.0 - показывает КУДА может пойти цена, но не ЧТО делают киты)
        liq_dir = signals["liquidity"].get("direction", {}).get("direction", "neutral")
        if liq_dir == "up":
            votes["BUY"] += 2.0
        elif liq_dir == "down":
            votes["SELL"] += 2.0
        
        # Market Structure (вес 1)
        trend = signals["structure"].get("trend", "range")
        if trend == "bullish":
            votes["BUY"] += 1
        elif trend == "bearish":
            votes["SELL"] += 1
        
        # TA (вес 0.5 - наименьший вес, так как может быть запаздывающим)
        ta_trend = signals["ta"].get("trend", "neutral")
        if ta_trend == "bullish":
            votes["BUY"] += 0.5
        elif ta_trend == "bearish":
            votes["SELL"] += 0.5
        
        # Логирование голосования для отладки
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"📊 ГОЛОСОВАНИЕ: BUY={votes['BUY']:.1f}, SELL={votes['SELL']:.1f}, WAIT={votes['WAIT']:.1f}")
        logger.info(f"   • SVD Intent: {svd_intent} (вес: {svd_weight:.1f}, conf: {svd_conf:.1f}, CVD: {signals['svd'].get('cvd', 0):.1f})")
        logger.info(f"   • Liquidity: {liq_dir} (вес: 2.0)")
        logger.info(f"   • Structure: {trend} (вес: 1.0)")
        logger.info(f"   • TA: {ta_trend} (вес: 0.5)")
        
        # Определение победителя
        max_votes = max(votes.values())
        if max_votes == 0:
            return "WAIT"
        
        # Если разница между BUY и SELL меньше 1, возвращаем WAIT (неопределенность)
        vote_diff = abs(votes["BUY"] - votes["SELL"])
        if vote_diff < 1.0:
            return "WAIT"
        
        winner = None
        for signal, count in votes.items():
            if count == max_votes:
                winner = signal
                break
        
        # SVD INTENT VETO: Блокируем противоречивые сигналы
        # Если киты распределяют (продают) → НЕЛЬЗЯ давать BUY
        # Если киты накапливают (покупают) → НЕЛЬЗЯ давать SELL
        if svd_intent == "distributing" and winner == "BUY" and svd_conf > 3:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"🚫 SVD VETO: Киты распределяют (CVD: {signals['svd'].get('cvd', 0):.1f}), "
                         f"блокирую BUY → WAIT (votes: BUY={votes['BUY']:.1f}, SELL={votes['SELL']:.1f})")
            return "WAIT"
        
        if svd_intent == "accumulating" and winner == "SELL" and svd_conf > 3:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"🚫 SVD VETO: Киты накапливают (CVD: {signals['svd'].get('cvd', 0):.1f}), "
                         f"блокирую SELL → WAIT (votes: BUY={votes['BUY']:.1f}, SELL={votes['SELL']:.1f})")
            return "WAIT"
        
        return winner if winner else "WAIT"
    
    def _calculate_confidence(self, signals):
        """Рассчитывает итоговый confidence (0-10) с учетом противоречий"""
        scores = []
        
        # Liquidity confidence (если есть)
        if "confidence" in signals["liquidity"]:
            scores.append(signals["liquidity"]["confidence"])
        
        # SVD confidence
        if "confidence" in signals["svd"]:
            svd_conf = signals["svd"]["confidence"]
            if svd_conf > 0:
                scores.append(svd_conf)
        
        # Оцениваем по согласованности и противоречиям
        liq_dir = signals["liquidity"].get("direction", {}).get("direction", "neutral")
        svd_intent = signals["svd"].get("intent", "unclear")
        trend = signals["structure"].get("trend", "range")
        ta_trend = signals["ta"].get("trend", "neutral")
        htf_trend1 = signals.get("htf", {}).get("htf1", "unknown")
        htf_trend2 = signals.get("htf", {}).get("htf2", "unknown")
        htf_liq1 = signals.get("htf_liq", {}).get("htf1", {}).get("direction", "neutral")
        htf_liq2 = signals.get("htf_liq", {}).get("htf2", {}).get("direction", "neutral")
        svd_phase = signals["svd"].get("phase", "discovery")
        fomo_flag = signals["svd"].get("fomo", False)
        panic_flag = signals["svd"].get("panic", False)
        strong_fomo = signals["svd"].get("strong_fomo", False)
        strong_panic = signals["svd"].get("strong_panic", False)
        sweeps = signals["liquidity"].get("sweeps", {"sweep_up": False, "sweep_down": False})
        
        agreement = 0
        contradictions = 0
        
        # Согласованность Liquidity и SVD
        if (liq_dir == "up" and svd_intent == "accumulating") or \
           (liq_dir == "down" and svd_intent == "distributing"):
            agreement += 2
        elif (liq_dir == "up" and svd_intent == "distributing") or \
             (liq_dir == "down" and svd_intent == "accumulating"):
            contradictions += 1  # Противоречие
        
        # Согласованность Structure и Liquidity
        if (trend == "bullish" and liq_dir == "up") or \
           (trend == "bearish" and liq_dir == "down"):
            agreement += 2
        elif (trend == "bullish" and liq_dir == "down") or \
             (trend == "bearish" and liq_dir == "up"):
            # КРИТИЧНО: НЕ штрафуем за structure contradiction если есть сильные сигналы разворота!
            # Если CVD reversal + execution + (RSI extreme ИЛИ sweep) → разворот тренда, structure устарела
            rsi = signals["ta"].get("rsi", 50)
            cvd_reversal = signals["svd"].get("cvd_reversal_detected", False)
            is_reversal_setup = (
                cvd_reversal and 
                svd_phase == "execution" and
                (rsi < 25 or rsi > 75 or sweeps.get("post_reversal"))
            )
            if not is_reversal_setup:
                contradictions += 1  # Противоречие (но не при развороте!)
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"🔄 Разворот тренда: игнорируем structure contradiction (bearish → BUY reversal)")
        elif trend == "range":
            agreement += 1
        
        # Согласованность TA и Structure
        if ta_trend == trend:
            agreement += 1
        elif (ta_trend == "bullish" and trend == "bearish") or \
             (ta_trend == "bearish" and trend == "bullish"):
            # НЕ штрафуем за TA/Structure contradiction если есть reversal setup
            rsi = signals["ta"].get("rsi", 50)
            cvd_reversal = signals["svd"].get("cvd_reversal_detected", False)
            is_reversal_setup = (
                cvd_reversal and 
                svd_phase == "execution" and
                (rsi < 25 or rsi > 75 or sweeps.get("post_reversal"))
            )
            if not is_reversal_setup:
                contradictions += 0.5  # Меньший вес для TA (но не при развороте!)

        # HTF bias: если совпадает — бонус, если против — небольшой штраф
        htf_bonus = 0
        for htf in [htf_trend1, htf_trend2]:
            if htf in ("bullish", "bearish"):
                if htf == trend:
                    htf_bonus += 0.3
                elif trend != "range" and htf != trend:
                    htf_bonus -= 0.3

        # HTF liquidity bias: если направление HTF ликвидности совпадает с локальным liq_dir — бонус
        for htf_liq in [htf_liq1, htf_liq2]:
            if htf_liq in ("up", "down"):
                if htf_liq == liq_dir:
                    htf_bonus += 0.2
                elif liq_dir != "neutral" and htf_liq != liq_dir:
                    htf_bonus -= 0.2
        
        # Базовый confidence от согласованности + HTF
        base_confidence = min(agreement * 1.5, 6) + htf_bonus
        
        # Штраф за противоречия (каждое противоречие снижает confidence на 1.5)
        contradiction_penalty = contradictions * 1.5
        base_confidence = max(0, base_confidence - contradiction_penalty)

        # Путь наименьшего сопротивления (path resistance)
        path_cost = self._compute_path_resistance(signals)
        signal_dir = signals.get("signal")
        if path_cost["up"] < path_cost["down"]:
            # вверх дешевле
            if signal_dir == "BUY":
                base_confidence += 0.3
            if liq_dir == "up":
                base_confidence += 0.2
        elif path_cost["down"] < path_cost["up"]:
            # вниз дешевле
            if signal_dir == "SELL":
                base_confidence += 0.3
            if liq_dir == "down":
                base_confidence += 0.2
        else:
            base_confidence -= 0.1  # неопределенность пути
        
        # Учет фаз SVD: execution (+), manipulation (-), distribution (+слегка)
        phase_bonus = 0
        if svd_phase == "execution":
            phase_bonus += 0.5
        elif svd_phase == "manipulation":
            phase_bonus -= 0.5
        elif svd_phase == "distribution":
            phase_bonus += 0.2
        base_confidence = max(0, min(10, base_confidence + phase_bonus))
        
        # CVD (Cumulative Volume Delta) подтверждение
        cvd_confirms = signals["svd"].get("cvd_confirms_intent", False)
        cvd_divergence = signals["svd"].get("cvd_divergence", False)
        cvd_reversal = signals["svd"].get("cvd_reversal_detected", False)
        cvd_slope = signals["svd"].get("cvd_slope", 0)
        cvd_value = signals["svd"].get("cvd", 0)
        
        # РАЗВОРОТ ТРЕНДА — сильный бонус за ранний вход
        if cvd_reversal:
            base_confidence += 1.5  # Большой бонус за обнаружение разворота
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🔄 РАЗВОРОТ ТРЕНДА: CVD={cvd_value:.1f}, slope={cvd_slope:.1f} → бонус +1.5")
        
        # RSI EXTREME — сильный бонус за перепроданность/перекупленность
        rsi = signals["ta"].get("rsi", 50)
        if rsi < 25:  # Экстремальная перепроданность
            rsi_bonus = 1.5  # Сильный бонус за разворот вверх
            base_confidence += rsi_bonus
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"📈 RSI OVERSOLD: {rsi:.1f} < 25 → бонус +{rsi_bonus}")
        elif rsi < 30:  # Перепроданность
            rsi_bonus = 1.0
            base_confidence += rsi_bonus
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"📈 RSI oversold: {rsi:.1f} < 30 → бонус +{rsi_bonus}")
        elif rsi > 75:  # Экстремальная перекупленность
            rsi_bonus = 1.5  # Сильный бонус за разворот вниз
            base_confidence += rsi_bonus
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"📉 RSI OVERBOUGHT: {rsi:.1f} > 75 → бонус +{rsi_bonus}")
        elif rsi > 70:  # Перекупленность
            rsi_bonus = 1.0
            base_confidence += rsi_bonus
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"📉 RSI overbought: {rsi:.1f} > 70 → бонус +{rsi_bonus}")
        
        # Если CVD подтверждает intent — бонус
        if cvd_confirms:
            base_confidence += 0.4
        # Если CVD дивергенция с ценой — предупреждение о возможном развороте
        if cvd_divergence:
            base_confidence -= 0.3
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️ CVD дивергенция обнаружена (slope: {cvd_slope:.2f})")
        # Если фаза distribution/trend, но CVD не подтверждает — штраф
        if svd_phase in ("distribution", "execution") and not cvd_confirms:
            base_confidence -= 0.3

        # Если есть confidence от модулей, усредняем
        if scores:
            avg_confidence = sum(scores) / len(scores)
            # Комбинируем: 60% от модулей, 40% от согласованности (уже с учетом противоречий)
            final_confidence = (avg_confidence * 0.6) + (base_confidence * 0.4)
        else:
            final_confidence = base_confidence
        
        # Доп. корректировки от fomo/panic (прокси поведения толпы)
        if fomo_flag:
            final_confidence -= 0.2
        if panic_flag:
            final_confidence -= 0.2
        if strong_fomo:
            final_confidence -= 0.3
        if strong_panic:
            final_confidence -= 0.3
        # Спуф подтвержден против направления — штраф; по направлению — небольшой бонус
        spoof_side = signals["svd"].get("spoof_wall", {}).get("side")
        spoof_confirmed = signals["svd"].get("spoof_confirmed", False)
        if spoof_confirmed and spoof_side:
            if spoof_side == "ask" and signals.get("signal") == "BUY":
                final_confidence -= 0.3
            if spoof_side == "bid" and signals.get("signal") == "SELL":
                final_confidence -= 0.3
            if spoof_side == "ask" and signals.get("signal") == "SELL":
                final_confidence += 0.1
            if spoof_side == "bid" and signals.get("signal") == "BUY":
                final_confidence += 0.1

        # Реакция на sweeps: свип вверх усиливает SELL, свип вниз усиливает BUY
        if sweeps.get("sweep_up") and signals.get("signal") == "SELL":
            final_confidence += 0.3
        if sweeps.get("sweep_down") and signals.get("signal") == "BUY":
            final_confidence += 0.3
        # Если свип задел ликвидность (стопы) — бонус
        if sweeps.get("hit_liquidity_above") and signals.get("signal") == "SELL":
            final_confidence += 0.2
        if sweeps.get("hit_liquidity_below") and signals.get("signal") == "BUY":
            final_confidence += 0.2
        # Если был пост-реверсал после свипа в сторону сигнала — еще бонус
        if sweeps.get("post_reversal") and signals.get("signal") in ("BUY", "SELL"):
            final_confidence += 0.2
        
        # BREAKOUT (медленный пробой) — сильный бонус
        breakout_up = signals.get("liquidity", {}).get("breakout_up", {})
        breakout_down = signals.get("liquidity", {}).get("breakout_down", {})
        
        if breakout_up.get("breakout_up") and signals.get("signal") == "BUY":
            # Сильный breakout (все свечи выше) = больший бонус
            if breakout_up.get("strong_breakout"):
                final_confidence += 1.0
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"📈 СИЛЬНЫЙ BREAKOUT UP: консолидация {breakout_up['consolidation_candles']} свечей → бонус +1.0")
            # Слабый breakout (большинство свечей выше)
            elif breakout_up.get("weak_breakout"):
                final_confidence += 0.5
        
        if breakout_down.get("breakout_down") and signals.get("signal") == "SELL":
            # Сильный breakout (все свечи ниже) = больший бонус
            if breakout_down.get("strong_breakout"):
                final_confidence += 1.0
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"📉 СИЛЬНЫЙ BREAKOUT DOWN: консолидация {breakout_down['consolidation_candles']} свечей → бонус +1.0")
            # Слабый breakout (большинство свечей ниже)
            elif breakout_down.get("weak_breakout"):
                final_confidence += 0.5
        
        # Штраф за низкое качество данных
        data_quality = signals.get("data_quality", {})
        overall_quality = data_quality.get("overall_quality", 1.0)
        if overall_quality < 0.8:
            quality_penalty = (0.8 - overall_quality) * 5  # до -4.0 при quality=0
            final_confidence -= quality_penalty
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"   📉 Штраф за качество данных: -{quality_penalty:.2f} (quality: {overall_quality:.2f})")
        
        # Volume Profile корректировки
        va_position = signals.get("liquidity", {}).get("va_position", "unknown")
        poc_info = signals.get("liquidity", {}).get("poc_info", {})
        signal_dir = signals.get("signal")
        
        # Если цена выше VAH и сигнал BUY — бычий подтверждение
        if va_position == "above_vah" and signal_dir == "BUY":
            final_confidence += 0.3
        # Если цена ниже VAL и сигнал SELL — медвежий подтверждение
        elif va_position == "below_val" and signal_dir == "SELL":
            final_confidence += 0.3
        # Если цена в Value Area — нейтрально (небольшой штраф за неопределенность)
        elif va_position == "in_value_area":
            final_confidence -= 0.1
        
        # PoC магнит: если цена близко к PoC — риск разворота
        if poc_info.get("near_poc", False):
            final_confidence -= 0.2  # Возможен разворот у PoC
        # PoC как поддержка/сопротивление
        if poc_info.get("poc_acts_as") == "support" and signal_dir == "BUY":
            final_confidence += 0.2
        elif poc_info.get("poc_acts_as") == "resistance" and signal_dir == "SELL":
            final_confidence += 0.2

        return min(max(final_confidence, 0), 10)
    
    def _compute_path_resistance(self, signals):
        """
        Приближенный расчет "стоимости" пути вверх/вниз:
        - path_cost из SVD (интеграл объёмов в стакане)
        - расстояние до ближайших кластеров ликвидности (stop_clusters, swing_liq, ATH/ATL)
        """
        path = signals.get("svd", {}).get("path_cost", {"up": 0.0, "down": 0.0})
        current_price = signals.get("current_price")
        liq = signals.get("liquidity", {})
        stop_clusters = liq.get("stop_clusters", [])
        swing_liq = liq.get("swing_liquidity", [])
        ath_atl = liq.get("ath_atl", {})

        nearest_above = None
        nearest_below = None
        if current_price:
            for src in (stop_clusters + swing_liq):
                price = src.get("price")
                t = src.get("type")
                if price is None:
                    continue
                if price > current_price and t == "buy_stops":
                    dist = (price - current_price) / current_price
                    if nearest_above is None or dist < nearest_above:
                        nearest_above = dist
                if price < current_price and t == "sell_stops":
                    dist = (current_price - price) / current_price
                    if nearest_below is None or dist < nearest_below:
                        nearest_below = dist
            # ATH/ATL
            ath = ath_atl.get("ath", {}).get("price")
            atl = ath_atl.get("atl", {}).get("price")
            if ath and ath > current_price:
                dist = (ath - current_price) / current_price
                if nearest_above is None or dist < nearest_above:
                    nearest_above = dist
            if atl and atl < current_price:
                dist = (current_price - atl) / current_price
                if nearest_below is None or dist < nearest_below:
                    nearest_below = dist

        # если нет уровней — считаем их далёкими
        if nearest_above is None:
            nearest_above = 1.0
        if nearest_below is None:
            nearest_below = 1.0

        # комбинированная "стоимость": стакан + расстояние до ближайшего кластера
        cost_up = path.get("up", 0.0) + nearest_above
        cost_down = path.get("down", 0.0) + nearest_below

        return {"up": cost_up, "down": cost_down}

    def _generate_explanation(self, signals, direction, confidence):
        """Генерирует объяснение на русском с учетом реальных данных"""
        parts = []
        
        liq_dir = signals["liquidity"].get("direction", {}).get("direction", "neutral")
        svd_intent = signals["svd"].get("intent", "unclear")
        trend = signals["structure"].get("trend", "range")
        delta = signals["svd"].get("delta", 0)
        absorption = signals["svd"].get("absorption", {})
        dom = signals["svd"].get("dom_imbalance", {})
        thin = signals["svd"].get("thin_zones", {})
        spoof = signals["svd"].get("spoof_wall", {})
        spoof_confirmed = signals["svd"].get("spoof_confirmed", False)
        spoof_duration_ms = signals["svd"].get("spoof_duration_ms", 0)
        dom_chasing = signals["svd"].get("dom_chasing", {"bid_chasing": False, "ask_chasing": False})
        sweeps = signals["liquidity"].get("sweeps", {"sweep_up": False, "sweep_down": False})
        fomo_flag = signals["svd"].get("fomo", False)
        panic_flag = signals["svd"].get("panic", False)
        strong_fomo = signals["svd"].get("strong_fomo", False)
        strong_panic = signals["svd"].get("strong_panic", False)
        phase = signals["svd"].get("phase", "discovery")
        htf_liq1 = signals.get("htf_liq", {}).get("htf1", {}).get("direction", "neutral")
        htf_liq2 = signals.get("htf_liq", {}).get("htf2", {}).get("direction", "neutral")
        
        if direction == "BUY":
            parts.append("Сигнал на покупку")
            if liq_dir == "up":
                parts.append("ликвидность указывает на движение вверх")
            # Используем реальные данные SVD
            if svd_intent == "accumulating":
                parts.append("крупные игроки накапливают позиции")
            elif svd_intent == "distributing":
                parts.append("⚠️ ВНИМАНИЕ: крупные игроки распределяют позиции (противоречие с сигналом)")
            if absorption.get("absorbing"):
                parts.append(f"обнаружено поглощение ({absorption.get('side', 'unknown')})")
            if dom.get("side") == "bid":
                parts.append("DOM дисбаланс в покупках")
            if thin.get("thin_above"):
                parts.append("сверху тонкая ликвидность — риск ускоренного роста")
            if spoof.get("side") == "bid" or spoof_confirmed:
                parts.append("возможен спуф на покупку (осторожно с ложной поддержкой)")
                if spoof_duration_ms:
                    parts.append(f"время жизни стены: {spoof_duration_ms/1000:.1f}с")
            if dom_chasing.get("bid_chasing"):
                parts.append("bids преследуют цену (chasing)")
        elif direction == "SELL":
            parts.append("Сигнал на продажу")
            if liq_dir == "down":
                parts.append("ликвидность указывает на движение вниз")
            # Используем реальные данные SVD
            if svd_intent == "distributing":
                parts.append("крупные игроки распределяют позиции")
            elif svd_intent == "accumulating":
                parts.append("⚠️ ВНИМАНИЕ: крупные игроки накапливают позиции (противоречие с сигналом)")
            if absorption.get("absorbing"):
                parts.append(f"обнаружено поглощение ({absorption.get('side', 'unknown')})")
            if dom.get("side") == "ask":
                parts.append("DOM дисбаланс в продажах")
            if thin.get("thin_below"):
                parts.append("снизу тонкая ликвидность — риск ускоренного падения")
            if spoof.get("side") == "ask" or spoof_confirmed:
                parts.append("возможен спуф на продажу (осторожно с ложным давлением)")
                if spoof_duration_ms:
                    parts.append(f"время жизни стены: {spoof_duration_ms/1000:.1f}с")
            if dom_chasing.get("ask_chasing"):
                parts.append("asks преследуют цену (chasing)")
        else:
            return "Недостаточно сигналов для принятия решения. Рекомендуется ожидание."

        # Sweep сигналы
        if sweeps.get("sweep_up"):
            parts.append("был свип вверх (прокол хай с возвратом)")
        if sweeps.get("sweep_down"):
            parts.append("был свип вниз (прокол лоу с возвратом)")

        # Флаги толпы
        if fomo_flag:
            parts.append("⚠️ FOMO: ускоренный приток покупок")
        if panic_flag:
            parts.append("⚠️ Panic: ускоренный приток продаж")
        if strong_fomo:
            parts.append("⚠️ Сильное FOMO: серия покупок с высоким ускорением")
        if strong_panic:
            parts.append("⚠️ Сильная паника: серия продаж с высоким ускорением")

        # Фаза
        parts.append(f"Фаза: {phase}")
        # HTF ликвидность
        parts.append(f"HTF ликвидность: 1) {htf_liq1}, 2) {htf_liq2}")
        
        return ". ".join(parts) + f" (уверенность: {confidence:.1f}/10)"
    
    def _generate_alternative_scenario(self, signals):
        """Генерирует альтернативный сценарий"""
        return "Если произойдет разворот структуры рынка, сигнал может измениться."
    
    def _calculate_levels(self, signals):
        """Рассчитывает уровни входа, целей и стоп-лосса на основе реальных данных"""
        levels = {
            "entry_zone": None,
            "targets": [],
            "invalidation": None
        }
        
        # Получаем данные
        liquidity_data = signals.get("liquidity", {})
        structure_data = signals.get("structure", {})
        direction = signals.get("signal", "WAIT")
        current_price = signals.get("current_price")  # Текущая цена
        
        # Находим ближайшие уровни ликвидности
        stop_clusters = liquidity_data.get("stop_clusters", [])
        swing_liq = liquidity_data.get("swing_liquidity", [])
        
        # Получаем swing points
        swings = structure_data.get("swings", {})
        highs = swings.get("highs", [])
        lows = swings.get("lows", [])
        
        # Если нет текущей цены, пытаемся получить из последней свечи или swing
        if current_price is None:
            if highs and lows:
                # Используем среднее между последним high и low
                last_high = highs[-1]["price"] if highs else 0
                last_low = lows[-1]["price"] if lows else 0
                current_price = (last_high + last_low) / 2 if (last_high > 0 and last_low > 0) else None
        
        # Определяем ближайшие уровни
        if direction == "BUY":
            targets = []
            
            # 1. Ищем ближайшие buy_stops выше текущей цены (приоритет)
            above_stops = []
            for cluster in stop_clusters:
                if cluster.get("type") == "buy_stops":
                    price = cluster.get("price", 0)
                    if price > 0 and (current_price is None or price > current_price):
                        above_stops.append(price)
            
            if above_stops:
                above_stops.sort()
                targets.append(f"${above_stops[0]:.2f}")  # Ближайшая цель
                if len(above_stops) > 1:
                    targets.append(f"${above_stops[1]:.2f}")  # Вторая цель
            
            # 2. Если нет стопов, используем swing highs выше цены
            if not targets and highs:
                above_highs = [s["price"] for s in highs if s.get("price", 0) > 0 and (current_price is None or s["price"] > current_price)]
                if above_highs:
                    above_highs.sort()
                    targets.append(f"${above_highs[0]:.2f}")
                    if len(above_highs) > 1:
                        targets.append(f"${above_highs[1]:.2f}")
            
            # 3. Если все еще нет, используем swing liquidity
            if not targets and swing_liq:
                above_swing = [s.get("price", 0) for s in swing_liq if s.get("type") == "buy_stops" and s.get("price", 0) > 0 and (current_price is None or s.get("price", 0) > current_price)]
                if above_swing:
                    above_swing.sort()
                    targets.append(f"${above_swing[0]:.2f}")
            
            # 4. Последний вариант - ATH
            if not targets:
                ath_atl = liquidity_data.get("ath_atl", {})
                if ath_atl.get("ath", {}).get("price"):
                    ath_price = ath_atl["ath"]["price"]
                    if current_price is None or ath_price > current_price:
                        targets.append(f"${ath_price:.2f} (ATH)")
            
            levels["targets"] = targets
            
            # Зона входа - текущая цена или ближайший swing low
            if current_price:
                if lows:
                    nearest_low = max([s["price"] for s in lows if s.get("price", 0) > 0 and s["price"] < current_price], default=None)
                    if nearest_low:
                        levels["entry_zone"] = f"${nearest_low:.2f} - ${current_price:.2f}"
                    else:
                        levels["entry_zone"] = f"${current_price:.2f}"
                else:
                    levels["entry_zone"] = f"${current_price:.2f}"
            
            # Стоп - ниже ближайшего swing low
            if lows:
                below_lows = [s["price"] for s in lows if s.get("price", 0) > 0]
                if below_lows:
                    min_low = min(below_lows)
                    levels["invalidation"] = f"${min_low * 0.998:.2f}"  # -0.2% от swing low
            
        elif direction == "SELL":
            targets = []
            
            # 1. Ищем ближайшие sell_stops ниже текущей цены (приоритет)
            below_stops = []
            for cluster in stop_clusters:
                if cluster.get("type") == "sell_stops":
                    price = cluster.get("price", 0)
                    if price > 0 and (current_price is None or price < current_price):
                        below_stops.append(price)
            
            if below_stops:
                below_stops.sort(reverse=True)
                targets.append(f"${below_stops[0]:.2f}")  # Ближайшая цель
                if len(below_stops) > 1:
                    targets.append(f"${below_stops[1]:.2f}")  # Вторая цель
            
            # 2. Если нет стопов, используем swing lows ниже цены
            if not targets and lows:
                below_lows = [s["price"] for s in lows if s.get("price", 0) > 0 and (current_price is None or s["price"] < current_price)]
                if below_lows:
                    below_lows.sort(reverse=True)
                    targets.append(f"${below_lows[0]:.2f}")
                    if len(below_lows) > 1:
                        targets.append(f"${below_lows[1]:.2f}")
            
            # 3. Если все еще нет, используем swing liquidity
            if not targets and swing_liq:
                below_swing = [s.get("price", 0) for s in swing_liq if s.get("type") == "sell_stops" and s.get("price", 0) > 0 and (current_price is None or s.get("price", 0) < current_price)]
                if below_swing:
                    below_swing.sort(reverse=True)
                    targets.append(f"${below_swing[0]:.2f}")
            
            # 4. Последний вариант - ATL
            if not targets:
                ath_atl = liquidity_data.get("ath_atl", {})
                if ath_atl.get("atl", {}).get("price"):
                    atl_price = ath_atl["atl"]["price"]
                    if current_price is None or atl_price < current_price:
                        targets.append(f"${atl_price:.2f} (ATL)")
            
            levels["targets"] = targets
            
            # Зона входа - текущая цена или ближайший swing high
            if current_price:
                if highs:
                    nearest_high = min([s["price"] for s in highs if s.get("price", 0) > 0 and s["price"] > current_price], default=None)
                    if nearest_high:
                        levels["entry_zone"] = f"${current_price:.2f} - ${nearest_high:.2f}"
                    else:
                        levels["entry_zone"] = f"${current_price:.2f}"
                else:
                    levels["entry_zone"] = f"${current_price:.2f}"
            
            # Стоп - выше ближайшего swing high
            if highs:
                above_highs = [s["price"] for s in highs if s.get("price", 0) > 0]
                if above_highs:
                    max_high = max(above_highs)
                    levels["invalidation"] = f"${max_high * 1.002:.2f}"  # +0.2% от swing high
        
        # Очищаем пустые значения
        if not levels["entry_zone"]:
            levels.pop("entry_zone", None)
        if not levels["targets"]:
            levels.pop("targets", None)
        if not levels["invalidation"]:
            levels.pop("invalidation", None)
        
        return levels

