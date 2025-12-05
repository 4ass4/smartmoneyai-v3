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


class SVDEngine:
    def __init__(self):
        # Память для трекинга спуфов и движения лучшего бид/аск
        self._prev_spoof = None
        self._prev_best = {"bid": None, "ask": None, "ts": None}

    def analyze(self, trades: list, orderbook: dict):
        """
        Главный метод SVD анализа.
        Вход:
            trades  — список последних сделок
            orderbook — стакан (bids/asks)
        """

        delta = compute_delta(trades)
        absorption = detect_absorption(trades, orderbook)
        aggression = detect_aggression(trades)
        velocity = detect_trade_velocity(trades)

        # Новый блок: дисбаланс стакана (DOM) и краткосрочные бакеты сделок
        dom_imbalance = compute_orderbook_imbalance(orderbook) if orderbook else {"imbalance": 1, "side": "neutral"}
        thin_zones = detect_thin_zones(orderbook) if orderbook else {"thin_above": None, "thin_below": None}
        # текущая цена и время из последней сделки, если есть
        current_price = trades[-1].get("price") if trades else None
        current_ts = trades[-1].get("timestamp") if trades else None
        spoof_wall = detect_spoof_wall(orderbook, current_price) if orderbook and current_price else {"side": None, "price": None, "volume": None, "factor": 1.0}
        bucket_metrics = bucket_trades(trades, bucket_seconds=5)

        # Определяем лучший бид/аск для DOM chasing
        best_bid = orderbook["bids"][0][0] if orderbook and orderbook.get("bids") else None
        best_ask = orderbook["asks"][0][0] if orderbook and orderbook.get("asks") else None
        
        score = svd_confidence_score(delta, absorption, aggression, velocity, dom_imbalance, bucket_metrics)

        # Smart Money intent с учетом доминирующей стороны стакана
        if delta < 0 and aggression["sell_aggression"] > aggression["buy_aggression"]:
            intent = "distributing"
        elif delta > 0 and aggression["buy_aggression"] > aggression["sell_aggression"]:
            intent = "accumulating"
        else:
            intent = "unclear"

        # Усиливаем intent, если DOM подтверждает сторону
        if dom_imbalance.get("side") == "bid" and intent == "accumulating":
            intent = "accumulating"
        elif dom_imbalance.get("side") == "ask" and intent == "distributing":
            intent = "distributing"

        # Простой трекинг спуфов: если была стена и исчезла без движения цены — подтверждаем spoof
        spoof_confirmed = False
        if self._prev_spoof and self._prev_spoof.get("side"):
            prev = self._prev_spoof
            if (not spoof_wall.get("side")) and current_price:
                price_move = abs(current_price - prev.get("price", current_price)) / current_price
                # ограничиваем по времени (если есть метка времени trades)
                time_ok = True
                if current_ts and prev.get("ts"):
                    time_ok = (current_ts - prev["ts"]) < 10_000  # 10 секунд
                if price_move < 0.0015 and time_ok:  # <0.15% движения — вероятный спуф
                    spoof_confirmed = True
        # обновляем память спуфа
        if spoof_wall.get("side"):
            self._prev_spoof = {"side": spoof_wall["side"], "price": spoof_wall.get("price"), "ts": current_ts}
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

        # Определяем фазу (грубая эвристика)
        phase = "discovery"
        if spoof_confirmed or spoof_wall.get("side"):
            phase = "manipulation"
        if absorption.get("absorbing") or velocity.get("velocity", 0) > 20 or aggression.get("buy_aggression", 0) + aggression.get("sell_aggression", 0) > 0:
            phase = "execution"
        if intent in ("accumulating", "distributing") and dom_imbalance.get("side") in ("bid", "ask"):
            phase = "distribution"

        return {
            "delta": delta,
            "absorption": absorption,
            "aggression": aggression,
            "velocity": velocity,
            "dom_imbalance": dom_imbalance,
            "thin_zones": thin_zones,
            "spoof_wall": spoof_wall,
            "spoof_confirmed": spoof_confirmed,
            "dom_chasing": dom_chasing,
            "buckets": bucket_metrics,
            "fomo": fomo_flag,
            "panic": panic_flag,
            "strong_fomo": strong_fomo,
            "strong_panic": strong_panic,
            "phase": phase,
            "intent": intent,
            "confidence": score
        }

