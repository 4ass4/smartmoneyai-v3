# modules/svd/svd_engine.py

from .delta import compute_delta
from .absorption import detect_absorption
from .aggression import detect_aggression
from .velocity import detect_trade_velocity
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
        
        score = svd_confidence_score(delta, absorption, aggression, velocity)

        # Smart Money intent
        if delta < 0 and aggression["sell_aggression"] > aggression["buy_aggression"]:
            intent = "distributing"
        elif delta > 0 and aggression["buy_aggression"] > aggression["sell_aggression"]:
            intent = "accumulating"
        else:
            intent = "unclear"

        return {
            "delta": delta,
            "absorption": absorption,
            "aggression": aggression,
            "velocity": velocity,
            "intent": intent,
            "confidence": score
        }

