from .stop_clusters import detect_stop_clusters
from .swing_liquidity import detect_swing_liquidity
from .ath_atl import detect_ath_atl_liquidity
from .liquidity_direction import detect_liquidity_direction
from .sweep_detector import detect_sweep, detect_historical_sweeps, detect_breakout
from .volume_profile import calculate_volume_profile, get_position_relative_to_value_area, get_poc_significance
from .swept_tracker import SweptLevelsTracker
from .touch_detector import detect_recent_touches, filter_touched_levels
import logging

logger = logging.getLogger(__name__)


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
        
        # Получаем текущую цену
        current_price = df['close'].iloc[-1] if not df.empty else None
        
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
        
        # НОВОЕ: Обнаруживаем исторические sweeps swing levels
        swing_highs = market_structure.get("swings", {}).get("highs", [])
        swing_lows = market_structure.get("swings", {}).get("lows", [])
        
        if current_price and len(df) >= 20:
            historical_sweeps = detect_historical_sweeps(
                df, 
                swing_highs, 
                swing_lows, 
                current_price,
                lookback_candles=100
            )
            
            # Помечаем исторические sweeps в tracker
            for hist_sweep in historical_sweeps:
                self.swept_tracker.mark_as_swept(
                    hist_sweep["price"],
                    hist_sweep["direction"],
                    reason=f"historical_sweep",
                    candles_ago=hist_sweep["candles_ago"]
                )
                logger.info(f"🎯 Исторический sweep обнаружен: ${hist_sweep['price']:.2f} "
                           f"({hist_sweep['direction']}, {hist_sweep['candles_ago']} свечей назад)")
        
        # НОВОЕ: Обнаружение недавно коснутых уровней (последние 20 свечей)
        # Это решает проблему когда цена УЖЕ коснулась уровня, но sweep detector не поймал
        touched_stop_clusters = detect_recent_touches(df, stop_clusters, lookback=20, tolerance_pct=0.2)
        touched_swing_levels = detect_recent_touches(df, swing_levels, lookback=20, tolerance_pct=0.2)
        
        # Помечаем touched levels в swept_tracker
        for touch in touched_stop_clusters["touched_levels"]:
            # Если уровень был touched недавно (< 20 свечей) → считаем swept
            # 20 свечей на 5м = ~1.5 часа (достаточно для обнаружения недавних касаний)
            if touch.get("candles_ago", 999) < 20:
                direction = "up" if touch["type"] == "buy_stops" else "down"
                self.swept_tracker.mark_as_swept(
                    touch["price"],
                    direction,
                    reason="recent_touch",
                    candles_ago=touch["candles_ago"]
                )
                logger.info(f"🎯 Недавнее касание обнаружено: ${touch['price']:.2f} "
                           f"({touch['type']}, {touch['candles_ago']} свечей назад) → помечен как swept")
        
        for touch in touched_swing_levels["touched_levels"]:
            # Если уровень был touched недавно (< 20 свечей) → считаем swept
            if touch.get("candles_ago", 999) < 20:
                direction = "up" if touch["type"] == "buy_stops" else "down"
                self.swept_tracker.mark_as_swept(
                    touch["price"],
                    direction,
                    reason="recent_touch",
                    candles_ago=touch["candles_ago"]
                )
                logger.info(f"🎯 Недавнее касание swing level: ${touch['price']:.2f} "
                           f"({touch['type']}, {touch['candles_ago']} свечей назад) → помечен как swept")
        
        # Фильтруем swept уровни из stop_clusters и swing_liquidity
        stop_clusters = self.swept_tracker.filter_swept_levels(stop_clusters, tolerance_pct=0.5)
        swing_levels = self.swept_tracker.filter_swept_levels(swing_levels, tolerance_pct=0.5)
        
        direction = detect_liquidity_direction(stop_clusters, swing_levels, ath_atl, df)
        
        # Обнаружение breakout (медленный пробой) для ближайших уровней ликвидности
        breakout_up = {"breakout_up": False}
        breakout_down = {"breakout_down": False}
        
        if current_price:
            # Проверяем breakout для ближайшего уровня сверху
            if direction.get("direction") == "up" and direction.get("nearest_up"):
                nearest_level_up = direction["nearest_up"]["price"]
                breakout_up = detect_breakout(df, nearest_level_up, direction="up", lookback=3)
                if breakout_up["breakout_up"]:
                    logger.info(f"📈 BREAKOUT UP обнаружен: ${nearest_level_up:.2f}, "
                               f"consolidation: {breakout_up['consolidation_candles']} свечей, "
                               f"strong: {breakout_up['strong_breakout']}")
            
            # Проверяем breakout для ближайшего уровня снизу
            if direction.get("direction") == "down" and direction.get("nearest_down"):
                nearest_level_down = direction["nearest_down"]["price"]
                breakout_down = detect_breakout(df, nearest_level_down, direction="down", lookback=3)
                if breakout_down["breakout_down"]:
                    logger.info(f"📉 BREAKOUT DOWN обнаружен: ${nearest_level_down:.2f}, "
                               f"consolidation: {breakout_down['consolidation_candles']} свечей, "
                               f"strong: {breakout_down['strong_breakout']}")
        
        # Volume Profile - распределение объёмов по ценам
        volume_profile = calculate_volume_profile(df, num_bins=50)
        
        # Положение относительно Value Area
        va_position = get_position_relative_to_value_area(current_price, volume_profile) if current_price else "unknown"
        
        # Значимость PoC
        poc_info = get_poc_significance(current_price, volume_profile) if current_price else {"near_poc": False, "distance_pct": None, "poc_acts_as": None}

        # Получаем список всех swept (отработанных) уровней
        swept_levels = self.swept_tracker.get_all_swept()
        
        # Объединяем все touched levels
        all_touched_levels = (
            touched_stop_clusters.get("touched_levels", []) + 
            touched_swing_levels.get("touched_levels", [])
        )
        
        return {
            "stop_clusters": stop_clusters,
            "swing_liquidity": swing_levels,
            "ath_atl": ath_atl,
            "sweeps": sweeps,
            "swept_levels": swept_levels,  # Отработанные уровни (теперь зоны интереса/support/resistance)
            "touched_levels": all_touched_levels,  # Недавно коснутые уровни
            "breakout_up": breakout_up,  # Обнаружение breakout вверх
            "breakout_down": breakout_down,  # Обнаружение breakout вниз
            "direction": direction,
            "volume_profile": volume_profile,
            "va_position": va_position,
            "poc_info": poc_info
        }

