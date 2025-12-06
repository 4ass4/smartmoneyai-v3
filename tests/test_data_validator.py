# tests/test_data_validator.py

"""
Unit тесты для DataQualityValidator
"""

import pytest
import pandas as pd
import time
from modules.utils.data_validator import DataQualityValidator


class TestDataQualityValidator:
    def setup_method(self):
        self.validator = DataQualityValidator()
    
    def test_valid_ohlcv(self):
        """Тест: валидные OHLCV данные"""
        df = pd.DataFrame({
            'timestamp': range(1000, 1100),
            'open': [100.0] * 100,
            'high': [101.0] * 100,
            'low': [99.0] * 100,
            'close': [100.5] * 100,
            'volume': [1000.0] * 100
        })
        
        result = self.validator.validate_ohlcv(df)
        
        assert result["valid"] == True
        assert result["quality_score"] > 0.7
    
    def test_empty_ohlcv(self):
        """Тест: пустой OHLCV"""
        df = pd.DataFrame()
        
        result = self.validator.validate_ohlcv(df)
        
        assert result["valid"] == False
        assert result["quality_score"] == 0
    
    def test_insufficient_candles(self):
        """Тест: недостаточно свечей"""
        df = pd.DataFrame({
            'timestamp': range(1000, 1010),
            'open': [100.0] * 10,
            'high': [101.0] * 10,
            'low': [99.0] * 10,
            'close': [100.5] * 10,
            'volume': [1000.0] * 10
        })
        
        result = self.validator.validate_ohlcv(df)
        
        assert result["valid"] == False
        assert "Insufficient candles" in str(result["issues"])
    
    def test_valid_orderbook(self):
        """Тест: валидный orderbook"""
        orderbook = {
            "bids": [[100.0, 10.0]] * 15,
            "asks": [[101.0, 10.0]] * 15,
            "timestamp": int(time.time() * 1000)
        }
        
        result = self.validator.validate_orderbook(orderbook, int(time.time() * 1000))
        
        assert result["valid"] == True
        assert result["quality_score"] > 0.7
    
    def test_crossed_orderbook(self):
        """Тест: crossed book (bid >= ask)"""
        orderbook = {
            "bids": [[102.0, 10.0]],
            "asks": [[101.0, 10.0]],
            "timestamp": int(time.time() * 1000)
        }
        
        result = self.validator.validate_orderbook(orderbook, int(time.time() * 1000))
        
        assert result["valid"] == False
        assert "Crossed book" in str(result["issues"])
    
    def test_stale_orderbook(self):
        """Тест: устаревший orderbook"""
        old_timestamp = int(time.time() * 1000) - 30000  # 30 секунд назад
        orderbook = {
            "bids": [[100.0, 10.0]] * 15,
            "asks": [[101.0, 10.0]] * 15,
            "timestamp": old_timestamp
        }
        
        result = self.validator.validate_orderbook(orderbook, int(time.time() * 1000))
        
        assert result["valid"] == False
        assert "stale" in str(result["issues"]).lower()
    
    def test_valid_trades(self):
        """Тест: валидные trades"""
        trades = [
            {"id": i, "price": 100.0 + i, "volume": 1.0, "side": "buy", "timestamp": 1000 + i}
            for i in range(30)
        ]
        
        result = self.validator.validate_trades(trades, int(time.time() * 1000))
        
        assert result["valid"] == True
        assert result["quality_score"] > 0.7
    
    def test_insufficient_trades(self):
        """Тест: недостаточно сделок"""
        trades = [
            {"id": i, "price": 100.0, "volume": 1.0, "side": "buy", "timestamp": 1000}
            for i in range(5)
        ]
        
        result = self.validator.validate_trades(trades)
        
        assert result["valid"] == False
        assert "Insufficient trades" in str(result["issues"])
    
    def test_validate_all(self):
        """Тест: комплексная валидация"""
        df = pd.DataFrame({
            'timestamp': range(1000, 1100),
            'open': [100.0] * 100,
            'high': [101.0] * 100,
            'low': [99.0] * 100,
            'close': [100.5] * 100,
            'volume': [1000.0] * 100
        })
        
        orderbook = {
            "bids": [[100.0, 10.0]] * 15,
            "asks": [[101.0, 10.0]] * 15,
            "timestamp": int(time.time() * 1000)
        }
        
        trades = [
            {"id": i, "price": 100.0 + i, "volume": 1.0, "side": "buy", "timestamp": 1000 + i}
            for i in range(30)
        ]
        
        result = self.validator.validate_all(df, orderbook, trades)
        
        assert result["all_valid"] == True
        assert result["overall_quality"] > 0.5

