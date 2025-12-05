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
        # Память для простого трекинга спуфов между вызовами
        self._prev_spoof = None

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
        # текущая цена из последней сделки, если есть
        current_price = trades[-1].get("price") if trades else None
        spoof_wall = detect_spoof_wall(orderbook, current_price) if orderbook and current_price else {"side": None, "price": None, "volume": None, "factor": 1.0}
        bucket_metrics = bucket_trades(trades, bucket_seconds=5)
        
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
                if price_move < 0.0015:  # <0.15% движения — вероятный спуф
                    spoof_confirmed = True
        # обновляем память
        self._prev_spoof = spoof_wall if spoof_wall.get("side") else None

        # FOMO / Panic прокси из бакетов
        fomo_flag = False
        panic_flag = False
        if bucket_metrics:
            last_delta = bucket_metrics.get("last_bucket_delta", 0)
            last_vel = bucket_metrics.get("last_bucket_velocity", 0)
            mean_vel = bucket_metrics.get("mean_velocity", 0)
            # FOMO: положительная дельта и скорость выше средней
            if last_delta > 0 and last_vel > mean_vel * 1.2 and last_vel > 5:
                fomo_flag = True
            # Panic: отрицательная дельта и скорость выше средней
            if last_delta < 0 and last_vel > mean_vel * 1.2 and last_vel > 5:
                panic_flag = True

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
            "buckets": bucket_metrics,
            "fomo": fomo_flag,
            "panic": panic_flag,
            "phase": phase,
            "intent": intent,
            "confidence": score
        }

