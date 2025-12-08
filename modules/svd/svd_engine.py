# modules/svd/svd_engine.py

from .delta import compute_delta
from .absorption import detect_absorption
from .aggression import detect_aggression
from .velocity import detect_trade_velocity
from .orderbook_imbalance import compute_orderbook_imbalance
from .orderbook_thin import detect_thin_zones
from .spoof_detector import detect_spoof_wall
from .trade_buckets import bucket_trades
from .svd_score import svd_confidence_score
from .orderbook_path import compute_path_cost
from .phase_tracker import PhaseTracker
from .cvd import CVDCalculator
from collections import deque


class SVDEngine:
    def __init__(self):
        # Память для трекинга спуфов и движения лучшего бид/аск
        self._prev_spoof = None  # {"side":..., "price":..., "ts_start":..., "ts_last":...}
        self._prev_best = {"bid": None, "ask": None, "ts": None}
        self._spoof_events = deque(maxlen=20)  # история подтвержденных спуфов
        self.phase_tracker = PhaseTracker(history_size=10)
        self.cvd_calculator = CVDCalculator()  # CVD для подтверждения трендов

    def analyze(self, trades: list, orderbook: dict, atr_pct=None):
        """
        Главный метод SVD анализа.
        Вход:
            trades  — список последних сделок
            orderbook — стакан (bids/asks)
            atr_pct — ATR в процентах для нормировки (optional)
        """
        from modules.utils.normalize import normalize_delta_on_atr, get_absorption_threshold, normalize_path_cost_on_atr

        delta = compute_delta(trades)
        # Нормировка дельты на волатильность
        if atr_pct:
            delta_normalized = normalize_delta_on_atr(delta, atr_pct)
        else:
            delta_normalized = delta
        
        absorption = detect_absorption(trades, orderbook, atr_pct=atr_pct)
        aggression = detect_aggression(trades)
        velocity = detect_trade_velocity(trades)

        # Новый блок: дисбаланс стакана (DOM) и краткосрочные бакеты сделок
        dom_imbalance = compute_orderbook_imbalance(orderbook) if orderbook else {"imbalance": 1, "side": "neutral"}
        thin_zones = detect_thin_zones(orderbook) if orderbook else {"thin_above": None, "thin_below": None}
        # текущая цена и время из последней сделки, если есть
        current_price = trades[-1].get("price") if trades else None
        current_ts = trades[-1].get("timestamp") if trades else None
        prev_price = trades[-2].get("price") if trades and len(trades) > 1 else None
        spoof_wall = detect_spoof_wall(orderbook, current_price) if orderbook and current_price else {"side": None, "price": None, "volume": None, "factor": 1.0}
        path_cost = compute_path_cost(orderbook, current_price, depth_levels=20, thin_zones=thin_zones) if orderbook and current_price else {"up": 0.0, "down": 0.0}
        bucket_metrics = bucket_trades(trades, bucket_seconds=5)

        # Определяем лучший бид/аск для DOM chasing
        best_bid = orderbook["bids"][0][0] if orderbook and orderbook.get("bids") else None
        best_ask = orderbook["asks"][0][0] if orderbook and orderbook.get("asks") else None
        
        score = svd_confidence_score(delta, absorption, aggression, velocity, dom_imbalance, bucket_metrics)
        
        # CVD (Cumulative Volume Delta) для подтверждения тренда
        cvd_data = self.cvd_calculator.calculate_cvd_from_trades(trades, reset_on_swing=False)
        cvd_value = cvd_data["cvd"]
        cvd_slope = cvd_data["cvd_slope"]
        cvd_divergence = cvd_data["divergence"]

        # Smart Money intent с учётом ОБЩЕГО CVD и CVD SLOPE
        # CVD value показывает ОБЩИЙ тренд накопления/распределения
        # CVD slope показывает НАПРАВЛЕНИЕ изменения (ускорение/замедление)
        
        # Пороги
        cvd_threshold = 5.0  # Порог для значимого общего CVD
        cvd_slope_threshold = 0.5  # Порог для значимого slope
        cvd_reversal_threshold = 1.5  # Порог для обнаружения разворота (снижен с 2.0 для более ранней detection)
        
        # ОБНАРУЖЕНИЕ РАЗВОРОТА ТРЕНДА (высокий приоритет!)
        # Если общий CVD отрицательный, НО slope сильно положительный → начало разворота вверх
        # Если общий CVD положительный, НО slope сильно отрицательный → начало разворота вниз
        reversal_detected = False
        
        if abs(cvd_value) > cvd_threshold:  # Есть значимый общий CVD
            # Разворот вверх: CVD отрицательный, но slope сильно положительный
            if cvd_value < 0 and cvd_slope > cvd_reversal_threshold:
                intent = "accumulating"  # Начало разворота вверх
                reversal_detected = True
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"🔄 РАЗВОРОТ ВВЕРХ: CVD={cvd_value:.1f} (отриц.), slope={cvd_slope:.1f} (растёт)")
            
            # Разворот вниз: CVD положительный, но slope сильно отрицательный
            elif cvd_value > 0 and cvd_slope < -cvd_reversal_threshold:
                intent = "distributing"  # Начало разворота вниз
                reversal_detected = True
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"🔄 РАЗВОРОТ ВНИЗ: CVD={cvd_value:.1f} (полож.), slope={cvd_slope:.1f} (падает)")
            
            # Нет разворота: используем общий CVD
            elif cvd_value > 0:
                intent = "accumulating"
            else:
                intent = "distributing"
        
        # ПРИОРИТЕТ 2: CVD slope (если общий CVD близок к 0)
        elif cvd_slope > cvd_slope_threshold:
            # CVD растёт → accumulating
            intent = "accumulating"
        elif cvd_slope < -cvd_slope_threshold:
            # CVD падает → distributing
            intent = "distributing"
        
        # ПРИОРИТЕТ 3: snapshot delta + aggression (если оба CVD незначимы)
        else:
            if delta < 0 and aggression["sell_aggression"] > aggression["buy_aggression"]:
                intent = "distributing"
            elif delta > 0 and aggression["buy_aggression"] > aggression["sell_aggression"]:
                intent = "accumulating"
            else:
                intent = "unclear"

        # КРИТИЧНО: Execution фаза → ПРИОРИТЕТ CVD slope!
        # Если execution + CVD slope растёт → accumulating (даже если CVD negative)
        # Если execution + CVD slope падает → distributing (даже если CVD positive)
        if phase == "execution":
            if cvd_slope > 1.0:  # Сильный рост CVD
                if intent != "accumulating":
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"⚡ EXECUTION: CVD slope +{cvd_slope:.1f} → intent перезаписан на ACCUMULATING")
                intent = "accumulating"
            elif cvd_slope < -1.0:  # Сильное падение CVD
                if intent != "distributing":
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"⚡ EXECUTION: CVD slope {cvd_slope:.1f} → intent перезаписан на DISTRIBUTING")
                intent = "distributing"
        
        # Усиливаем intent, если DOM подтверждает сторону
        if dom_imbalance.get("side") == "bid" and intent == "accumulating":
            intent = "accumulating"
        elif dom_imbalance.get("side") == "ask" and intent == "distributing":
            intent = "distributing"
        
        # CVD подтверждение: проверяем согласованность CVD slope с intent
        cvd_confirms_intent = False
        is_pullback_or_bounce = False
        
        if intent == "accumulating":
            if cvd_slope > 0:
                cvd_confirms_intent = True  # Накопление ускоряется
            elif cvd_slope < -cvd_slope_threshold and cvd_value > cvd_threshold:
                # Накопление замедляется (pullback), но общий тренд накопление
                is_pullback_or_bounce = True
                cvd_confirms_intent = True  # Не штрафуем, это нормально
        elif intent == "distributing":
            if cvd_slope < 0:
                cvd_confirms_intent = True  # Распределение ускоряется
            elif cvd_slope > cvd_slope_threshold and cvd_value < -cvd_threshold:
                # Распределение замедляется (bounce), но общий тренд распределение
                is_pullback_or_bounce = True
                cvd_confirms_intent = True  # Не штрафуем, это нормально
        elif intent == "unclear":
            cvd_confirms_intent = True  # Для unclear не штрафуем

        # Трекинг спуфов: время жизни и исчезновение
        spoof_confirmed = False
        spoof_duration = 0
        if self._prev_spoof and self._prev_spoof.get("side"):
            prev = self._prev_spoof
            if (not spoof_wall.get("side")) and current_price:
                price_move = abs(current_price - prev.get("price", current_price)) / current_price
                time_ok = True
                if current_ts and prev.get("ts_last"):
                    spoof_duration = (current_ts - prev["ts_start"]) if prev.get("ts_start") else (current_ts - prev.get("ts_last", current_ts))
                    time_ok = spoof_duration < 15_000  # <15s жизнь стены
                if price_move < 0.0015 and time_ok:
                    spoof_confirmed = True
                    # логируем событие
                    self._spoof_events.append({
                        "side": prev.get("side"),
                        "price": prev.get("price"),
                        "duration_ms": spoof_duration,
                        "ts": current_ts
                    })
        # обновляем память спуфа
        if spoof_wall.get("side"):
            # если стена та же сторона, продлеваем ts_last, ts_start
            if self._prev_spoof and self._prev_spoof.get("side") == spoof_wall.get("side"):
                start_ts = self._prev_spoof.get("ts_start", current_ts)
            else:
                start_ts = current_ts
            self._prev_spoof = {
                "side": spoof_wall["side"],
                "price": spoof_wall.get("price"),
                "ts_start": start_ts,
                "ts_last": current_ts
            }
        else:
            self._prev_spoof = None

        # DOM chasing: лучшая bid/ask двигается вслед за ценой
        dom_chasing = {"bid_chasing": False, "ask_chasing": False}
        if best_bid and best_ask:
            if self._prev_best["bid"] is not None and best_bid > self._prev_best["bid"]:
                dom_chasing["bid_chasing"] = True
            if self._prev_best["ask"] is not None and best_ask < self._prev_best["ask"]:
                dom_chasing["ask_chasing"] = True
        # обновляем память лучших цен
        self._prev_best = {"bid": best_bid, "ask": best_ask, "ts": current_ts}

        # FOMO / Panic прокси из бакетов
        fomo_flag = False
        panic_flag = False
        strong_fomo = False
        strong_panic = False
        price_move_pct = 0
        if current_price and prev_price and prev_price != 0:
            price_move_pct = abs(current_price - prev_price) / prev_price * 100
        if bucket_metrics:
            last_delta = bucket_metrics.get("last_bucket_delta", 0)
            last_vel = bucket_metrics.get("last_bucket_velocity", 0)
            mean_vel = bucket_metrics.get("mean_velocity", 0)
            pos_streak = bucket_metrics.get("pos_streak", 0)
            neg_streak = bucket_metrics.get("neg_streak", 0)
            # FOMO: серия положительных бакетов и скорость выше средней
            if (last_delta > 0 or pos_streak >= 2) and last_vel > max(mean_vel * 1.1, 5):
                fomo_flag = True
            # Panic: серия отрицательных бакетов и скорость выше средней
            if (last_delta < 0 or neg_streak >= 2) and last_vel > max(mean_vel * 1.1, 5):
                panic_flag = True
            # Усиленная метка: длинные серии и сильное ускорение
            if pos_streak >= 3 and last_vel > max(mean_vel * 1.5, 8):
                strong_fomo = True
            if neg_streak >= 3 and last_vel > max(mean_vel * 1.5, 8):
                strong_panic = True
            # Усиление через волатильность между последними сделками
            if price_move_pct > 0.25 and fomo_flag:
                strong_fomo = True
            if price_move_pct > 0.25 and panic_flag:
                strong_panic = True

        # Нормировка path_cost на ATR
        if atr_pct:
            path_cost_normalized = normalize_path_cost_on_atr(path_cost.get("up", 0), path_cost.get("down", 0), atr_pct)
        else:
            path_cost_normalized = path_cost
        
        # Определяем фазу (улучшенная эвристика с приоритетами)
        detected_phase = "discovery"
        
        # Приоритет 1: execution (сильные признаки исполнения)
        if absorption.get("absorbing") or velocity.get("velocity", 0) > 20:
            detected_phase = "execution"
        # Приоритет 2: manipulation (спуфы, тонкие зоны)
        elif spoof_confirmed or spoof_wall.get("side"):
            detected_phase = "manipulation"
        # Приоритет 3: distribution (явное накопление/распределение с DOM подтверждением)
        elif intent in ("accumulating", "distributing") and dom_imbalance.get("side") in ("bid", "ask"):
            detected_phase = "distribution"
        # По умолчанию: discovery
        else:
            detected_phase = "discovery"
        
        # Обновляем PhaseTracker с новой фазой
        phase_info = self.phase_tracker.update_phase(detected_phase, current_ts)
        phase = phase_info["phase"]
        phase_confidence = phase_info["phase_confidence"]
        phase_changed = phase_info["phase_changed"]

        return {
            "delta": delta,
            "delta_normalized": delta_normalized,  # Нормированная дельта
            "cvd": cvd_value,  # CVD (накопительная дельта)
            "cvd_slope": cvd_slope,  # Наклон CVD (trend)
            "cvd_divergence": cvd_divergence,  # Дивергенция CVD с ценой
            "cvd_confirms_intent": cvd_confirms_intent,  # CVD подтверждает intent
            "cvd_reversal_detected": reversal_detected,  # Обнаружен разворот тренда
            "is_pullback_or_bounce": is_pullback_or_bounce,  # Накопление с откатом или распределение с отскоком
            "absorption": absorption,
            "aggression": aggression,
            "velocity": velocity,
            "dom_imbalance": dom_imbalance,
            "thin_zones": thin_zones,
            "spoof_wall": spoof_wall,
            "spoof_confirmed": spoof_confirmed,
            "spoof_duration_ms": spoof_duration,
            "spoof_events": list(self._spoof_events),
            "dom_chasing": dom_chasing,
            "buckets": bucket_metrics,
            "path_cost": path_cost,
            "path_cost_normalized": path_cost_normalized,  # Нормированный path cost
            "fomo": fomo_flag,
            "panic": panic_flag,
            "strong_fomo": strong_fomo,
            "strong_panic": strong_panic,
            "phase": phase,
            "phase_info": phase_info,  # Полная информация о фазе
            "phase_confidence": phase_confidence,
            "phase_changed": phase_changed,
            "expected_next_phases": self.phase_tracker.get_expected_next_phase(),
            "intent": intent,
            "confidence": score,
            "atr_pct": atr_pct  # Для справки
        }

