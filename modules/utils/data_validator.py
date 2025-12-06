# modules/utils/data_validator.py

import time
import logging

logger = logging.getLogger(__name__)


class DataQualityValidator:
    """
    Валидатор качества и свежести рыночных данных
    """
    
    def __init__(self, config=None):
        self.config = config
        # Максимальный возраст данных в секундах
        self.max_age_ohlcv = getattr(config, 'MAX_AGE_OHLCV_SECONDS', 300) if config else 300
        self.max_age_orderbook = getattr(config, 'MAX_AGE_ORDERBOOK_SECONDS', 10) if config else 10
        self.max_age_trades = getattr(config, 'MAX_AGE_TRADES_SECONDS', 30) if config else 30
        # Минимальная глубина данных
        self.min_orderbook_levels = getattr(config, 'MIN_ORDERBOOK_LEVELS', 10) if config else 10
        self.min_trades_count = getattr(config, 'MIN_TRADES_COUNT', 20) if config else 20
        self.min_ohlcv_candles = getattr(config, 'MIN_OHLCV_CANDLES', 50) if config else 50
    
    def validate_ohlcv(self, df, fetch_timestamp=None):
        """
        Валидация OHLCV данных
        
        Returns:
            dict: {"valid": bool, "quality_score": 0-1, "issues": []}
        """
        issues = []
        quality_score = 1.0
        
        if df is None or df.empty:
            return {"valid": False, "quality_score": 0, "issues": ["OHLCV data is empty"]}
        
        # Проверка количества свечей
        if len(df) < self.min_ohlcv_candles:
            issues.append(f"Insufficient candles: {len(df)} < {self.min_ohlcv_candles}")
            quality_score -= 0.3
        
        # Проверка свежести (если есть timestamp последней свечи)
        if fetch_timestamp and 'timestamp' in df.columns:
            last_candle_ts = df['timestamp'].iloc[-1]
            age_seconds = (fetch_timestamp - last_candle_ts) / 1000  # ms to seconds
            if age_seconds > self.max_age_ohlcv:
                issues.append(f"OHLCV data is stale: {age_seconds:.0f}s old")
                quality_score -= 0.4
        
        # Проверка на пропуски (gaps)
        if 'timestamp' in df.columns and len(df) > 1:
            time_diffs = df['timestamp'].diff().dropna()
            median_diff = time_diffs.median()
            gaps = time_diffs[time_diffs > median_diff * 2]
            if len(gaps) > 0:
                issues.append(f"Found {len(gaps)} time gaps in OHLCV")
                quality_score -= 0.1
        
        # Проверка на нулевые/невалидные данные
        if (df[['open', 'high', 'low', 'close']] <= 0).any().any():
            issues.append("Found zero or negative prices in OHLCV")
            quality_score -= 0.2
        
        valid = quality_score > 0.3
        quality_score = max(0, quality_score)
        
        if not valid:
            logger.warning(f"OHLCV validation failed: {issues}")
        
        return {
            "valid": valid,
            "quality_score": quality_score,
            "issues": issues,
            "candle_count": len(df)
        }
    
    def validate_orderbook(self, orderbook, fetch_timestamp=None):
        """
        Валидация orderbook данных
        
        Returns:
            dict: {"valid": bool, "quality_score": 0-1, "issues": []}
        """
        issues = []
        quality_score = 1.0
        
        if not orderbook or not isinstance(orderbook, dict):
            return {"valid": False, "quality_score": 0, "issues": ["Orderbook is empty or invalid"]}
        
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])
        
        # Проверка наличия данных
        if not bids or not asks:
            return {"valid": False, "quality_score": 0, "issues": ["Orderbook has no bids or asks"]}
        
        # Проверка глубины
        if len(bids) < self.min_orderbook_levels:
            issues.append(f"Insufficient bid levels: {len(bids)} < {self.min_orderbook_levels}")
            quality_score -= 0.2
        if len(asks) < self.min_orderbook_levels:
            issues.append(f"Insufficient ask levels: {len(asks)} < {self.min_orderbook_levels}")
            quality_score -= 0.2
        
        # Проверка свежести
        if fetch_timestamp and 'timestamp' in orderbook:
            age_seconds = (fetch_timestamp - orderbook['timestamp']) / 1000
            if age_seconds > self.max_age_orderbook:
                issues.append(f"Orderbook is stale: {age_seconds:.1f}s old")
                quality_score -= 0.5
        
        # Проверка на crossed book (bid > ask)
        best_bid = bids[0][0] if bids else 0
        best_ask = asks[0][0] if asks else float('inf')
        if best_bid >= best_ask:
            issues.append(f"Crossed book detected: bid {best_bid} >= ask {best_ask}")
            quality_score -= 0.3
        
        # Проверка на нулевые объемы
        zero_bids = sum(1 for _, vol in bids if vol <= 0)
        zero_asks = sum(1 for _, vol in asks if vol <= 0)
        if zero_bids > 0 or zero_asks > 0:
            issues.append(f"Found zero volumes: {zero_bids} bids, {zero_asks} asks")
            quality_score -= 0.1
        
        valid = quality_score > 0.3
        quality_score = max(0, quality_score)
        
        if not valid:
            logger.warning(f"Orderbook validation failed: {issues}")
        
        return {
            "valid": valid,
            "quality_score": quality_score,
            "issues": issues,
            "bid_levels": len(bids),
            "ask_levels": len(asks),
            "spread_pct": ((best_ask - best_bid) / best_bid * 100) if best_bid > 0 else 0
        }
    
    def validate_trades(self, trades, fetch_timestamp=None):
        """
        Валидация trades данных
        
        Returns:
            dict: {"valid": bool, "quality_score": 0-1, "issues": []}
        """
        issues = []
        quality_score = 1.0
        
        if not trades or not isinstance(trades, list):
            return {"valid": False, "quality_score": 0, "issues": ["Trades data is empty or invalid"]}
        
        # Проверка количества сделок
        if len(trades) < self.min_trades_count:
            issues.append(f"Insufficient trades: {len(trades)} < {self.min_trades_count}")
            quality_score -= 0.3
        
        # Проверка свежести
        if fetch_timestamp and trades and 'timestamp' in trades[-1]:
            last_trade_ts = trades[-1]['timestamp']
            age_seconds = (fetch_timestamp - last_trade_ts) / 1000
            if age_seconds > self.max_age_trades:
                issues.append(f"Trades data is stale: {age_seconds:.1f}s old")
                quality_score -= 0.4
        
        # Проверка на дубликаты по ID (если есть)
        if trades and 'id' in trades[0]:
            ids = [t.get('id') for t in trades if 'id' in t]
            if len(ids) != len(set(ids)):
                issues.append("Duplicate trade IDs detected")
                quality_score -= 0.1
        
        # Проверка на валидные данные
        invalid_count = 0
        for t in trades:
            if not isinstance(t, dict):
                invalid_count += 1
                continue
            if 'price' not in t or 'volume' not in t:
                invalid_count += 1
                continue
            if t.get('price', 0) <= 0 or t.get('volume', 0) <= 0:
                invalid_count += 1
        
        if invalid_count > 0:
            issues.append(f"Found {invalid_count} invalid trades")
            quality_score -= min(0.3, invalid_count / len(trades))
        
        valid = quality_score > 0.3
        quality_score = max(0, quality_score)
        
        if not valid:
            logger.warning(f"Trades validation failed: {issues}")
        
        return {
            "valid": valid,
            "quality_score": quality_score,
            "issues": issues,
            "trade_count": len(trades)
        }
    
    def validate_all(self, ohlcv_df, orderbook, trades, fetch_timestamp=None):
        """
        Комплексная валидация всех данных
        
        Returns:
            dict: {
                "all_valid": bool,
                "overall_quality": 0-1,
                "ohlcv": {...},
                "orderbook": {...},
                "trades": {...}
            }
        """
        if fetch_timestamp is None:
            fetch_timestamp = int(time.time() * 1000)
        
        ohlcv_result = self.validate_ohlcv(ohlcv_df, fetch_timestamp)
        orderbook_result = self.validate_orderbook(orderbook, fetch_timestamp)
        trades_result = self.validate_trades(trades, fetch_timestamp)
        
        # Общая оценка качества (средневзвешенная)
        weights = {"ohlcv": 0.3, "orderbook": 0.4, "trades": 0.3}
        overall_quality = (
            ohlcv_result["quality_score"] * weights["ohlcv"] +
            orderbook_result["quality_score"] * weights["orderbook"] +
            trades_result["quality_score"] * weights["trades"]
        )
        
        all_valid = ohlcv_result["valid"] and orderbook_result["valid"] and trades_result["valid"]
        
        result = {
            "all_valid": all_valid,
            "overall_quality": overall_quality,
            "ohlcv": ohlcv_result,
            "orderbook": orderbook_result,
            "trades": trades_result,
            "timestamp": fetch_timestamp
        }
        
        if not all_valid:
            logger.warning(f"Data validation failed. Overall quality: {overall_quality:.2f}")
        else:
            logger.info(f"Data validation passed. Overall quality: {overall_quality:.2f}")
        
        return result

