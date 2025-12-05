# modules/liquidity/imbalance.py

def calculate_liquidity_imbalance(orderbook):
    """
    Дисбаланс между:
    - кол-вом ликвидности выше цены
    - кол-вом ликвидности ниже цены
    """

    up = sum(v for _, v in orderbook["asks"])
    down = sum(v for _, v in orderbook["bids"])

    return {"up": up, "down": down}

