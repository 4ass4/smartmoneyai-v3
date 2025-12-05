# modules/svd/svd_engine.py

from .delta import compute_delta
from .absorption import detect_absorption
from .aggression import detect_aggression
from .velocity import detect_trade_velocity
from .orderbook_imbalance import compute_orderbook_imbalance
from .trade_buckets import bucket_trades
from .svd_score import svd_confidence_score


class SVDEngine:

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

        return {
            "delta": delta,
            "absorption": absorption,
            "aggression": aggression,
            "velocity": velocity,
            "dom_imbalance": dom_imbalance,
            "buckets": bucket_metrics,
            "intent": intent,
            "confidence": score
        }

