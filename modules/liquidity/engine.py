# modules/liquidity/engine.py

from .detector_stops import detect_stop_clusters
from .detector_heatmap import detect_liquidity_heatmap
from .imbalance import calculate_liquidity_imbalance
from .scoring import score_liquidity_map


class LiquidityEngine:

    def __init__(self):
        pass

    def analyze(self, orderbook: dict, price: float):
        """
        Главный метод модуля.
        На вход: стакан: bids/asks, best bid/ask, объемы.
        На выход: структура ликвидности + направление движения.
        """

        # 1. Ищем скопления стопов / ликвидаций
        stops = detect_stop_clusters(orderbook, price)

        # 2. Анализ лимиток — где стоят крупные лимитные игроки
        heatmap = detect_liquidity_heatmap(orderbook)

        # 3. Дисбаланс ликвидности вверх/вниз
        imbalance = calculate_liquidity_imbalance(orderbook)

        # 4. Итоговый Confidence Score
        score = score_liquidity_map(stops, heatmap, imbalance)

        # 5. Предсказание направления
        if imbalance["up"] > imbalance["down"]:
            direction = "bullish"
        elif imbalance["down"] > imbalance["up"]:
            direction = "bearish"
        else:
            direction = "neutral"

        # Финальный пакет
        return {
            "direction": direction,
            "imbalance": imbalance,
            "stops": stops,
            "heatmap": heatmap,
            "confidence": score
        }
