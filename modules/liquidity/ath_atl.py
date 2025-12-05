# modules/liquidity/ath_atl.py

# Определение зон ликвидности у исторических экстремумов.


def detect_ath_atl_liquidity(df):
    high = df['high'].max()
    low = df['low'].min()

    return {
        "ath": {"price": high, "type": "buy_stops"},
        "atl": {"price": low, "type": "sell_stops"}
    }

