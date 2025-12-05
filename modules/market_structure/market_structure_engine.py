from .swings import detect_swings
from .trend import detect_trend
from .range import detect_range
from .fvg import detect_fvg
from .orderblocks import detect_orderblocks


class MarketStructureEngine:

    def analyze(self, df):
        """
        df — pandas DataFrame OHLCV (последние 200–300 свечей)
        """

        swings = detect_swings(df)
        trend = detect_trend(swings)
        range_info = detect_range(swings, df)
        fvg = detect_fvg(df)
        orderblocks = detect_orderblocks(swings, df)

        return {
            "trend": trend,
            "swings": swings,
            "range": range_info,
            "fvg": fvg,
            "orderblocks": orderblocks
        }

