from .stop_clusters import detect_stop_clusters
from .swing_liquidity import detect_swing_liquidity
from .ath_atl import detect_ath_atl_liquidity
from .liquidity_direction import detect_liquidity_direction
from .sweep_detector import detect_sweep


class LiquidityEngine:

    def analyze(self, df, market_structure):
        """
        df — OHLCV DataFrame
        market_structure — данные из MarketStructureEngine
        """

        stop_clusters = detect_stop_clusters(df)
        swing_levels = detect_swing_liquidity(market_structure)
        ath_atl = detect_ath_atl_liquidity(df)
        # Список стопов выше/ниже для свип-детектора
        stops_above = [c["price"] for c in stop_clusters if c.get("type") == "buy_stops"]
        stops_below = [c["price"] for c in stop_clusters if c.get("type") == "sell_stops"]
        sweeps = detect_sweep(df, stop_prices_above=stops_above, stop_prices_below=stops_below)
        direction = detect_liquidity_direction(stop_clusters, swing_levels, ath_atl, df)

        return {
            "stop_clusters": stop_clusters,
            "swing_liquidity": swing_levels,
            "ath_atl": ath_atl,
            "sweeps": sweeps,
            "direction": direction
        }

