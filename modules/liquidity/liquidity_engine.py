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
        sweeps = detect_sweep(df)
        direction = detect_liquidity_direction(stop_clusters, swing_levels, ath_atl, df)

        return {
            "stop_clusters": stop_clusters,
            "swing_liquidity": swing_levels,
            "ath_atl": ath_atl,
            "sweeps": sweeps,
            "direction": direction
        }

