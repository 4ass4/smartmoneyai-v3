from .stop_clusters import detect_stop_clusters
from .swing_liquidity import detect_swing_liquidity
from .ath_atl import detect_ath_atl_liquidity
from .liquidity_direction import detect_liquidity_direction
from .sweep_detector import detect_sweep
from .volume_profile import calculate_volume_profile, get_position_relative_to_value_area, get_poc_significance
from .swept_tracker import SweptLevelsTracker


class LiquidityEngine:
    
    def __init__(self):
        # Трекер отработанных (swept) уровней
        self.swept_tracker = SweptLevelsTracker(expiry_hours=24)

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
        
        # Помечаем swept уровни (если был sweep с post_reversal)
        if sweeps.get("post_reversal"):
            for swept in sweeps.get("swept_prices", []):
                self.swept_tracker.mark_as_swept(
                    swept["price"], 
                    swept["direction"], 
                    reason="sweep_with_reversal"
                )
        
        # Фильтруем swept уровни из stop_clusters и swing_liquidity
        stop_clusters = self.swept_tracker.filter_swept_levels(stop_clusters, tolerance_pct=0.5)
        swing_levels = self.swept_tracker.filter_swept_levels(swing_levels, tolerance_pct=0.5)
        
        direction = detect_liquidity_direction(stop_clusters, swing_levels, ath_atl, df)
        
        # Volume Profile - распределение объёмов по ценам
        volume_profile = calculate_volume_profile(df, num_bins=50)
        current_price = df['close'].iloc[-1] if not df.empty else None
        
        # Положение относительно Value Area
        va_position = get_position_relative_to_value_area(current_price, volume_profile) if current_price else "unknown"
        
        # Значимость PoC
        poc_info = get_poc_significance(current_price, volume_profile) if current_price else {"near_poc": False, "distance_pct": None, "poc_acts_as": None}

        # Получаем список всех swept (отработанных) уровней
        swept_levels = self.swept_tracker.get_all_swept()
        
        return {
            "stop_clusters": stop_clusters,
            "swing_liquidity": swing_levels,
            "ath_atl": ath_atl,
            "sweeps": sweeps,
            "swept_levels": swept_levels,  # Отработанные уровни (теперь зоны интереса/support/resistance)
            "direction": direction,
            "volume_profile": volume_profile,
            "va_position": va_position,
            "poc_info": poc_info
        }

