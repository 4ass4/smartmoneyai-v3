# modules/liquidity/detector_heatmap.py

def detect_liquidity_heatmap(orderbook):
    """
    Находим крупные лимитные блоки (icebergs):
    - уровни, где стоит крупная ликвидность
    - уровни, где маркетмейкеры собирают стопы
    """

    heatmap = {"strong_levels": []}

    threshold = max(orderbook["avg_bid"], orderbook["avg_ask"]) * 5

    for side in ("bids", "asks"):
        for level_price, volume in orderbook[side]:
            if volume > threshold:
                heatmap["strong_levels"].append({
                    "price": level_price,
                    "volume": volume,
                    "side": side
                })

    return heatmap

