# tests/test_conflict_detector.py

"""
Unit тесты для ConflictDetector
"""

import pytest
from modules.decision.conflict_detector import ConflictDetector


class TestConflictDetector:
    def setup_method(self):
        self.detector = ConflictDetector()
    
    def test_no_conflicts(self):
        """Тест: нет конфликтов"""
        signals = {
            "liquidity": {"direction": {"direction": "up"}},
            "svd": {"intent": "accumulating", "phase": "execution"},
            "structure": {"trend": "bullish"},
            "ta": {"trend": "bullish"},
            "signal": "BUY"
        }
        
        result = self.detector.detect_conflicts(signals)
        
        assert result["has_conflicts"] == False
        assert result["conflict_count"] == 0
        assert result["severity"] == "none"
    
    def test_critical_conflict_liquidity_vs_svd(self):
        """Тест: критичный конфликт liquidity vs SVD"""
        signals = {
            "liquidity": {"direction": {"direction": "up"}},
            "svd": {"intent": "distributing", "phase": "distribution"},
            "structure": {"trend": "range"},
            "ta": {"trend": "neutral"},
            "signal": "BUY"
        }
        
        result = self.detector.detect_conflicts(signals)
        
        assert result["has_conflicts"] == True
        assert result["critical_conflicts"] >= 1
        assert result["severity"] in ("major", "critical")
    
    def test_force_wait_on_critical(self):
        """Тест: force WAIT при критичных конфликтах"""
        signals = {
            "liquidity": {"direction": {"direction": "up"}},
            "svd": {"intent": "distributing", "phase": "manipulation"},
            "structure": {"trend": "range"},
            "ta": {"trend": "neutral"},
            "signal": "BUY"
        }
        
        result = self.detector.detect_conflicts(signals)
        should_wait, reason = self.detector.should_force_wait(result)
        
        assert should_wait == True
        assert "критич" in reason.lower() or "conflict" in reason.lower()
    
    def test_dom_conflict(self):
        """Тест: конфликт signal vs DOM"""
        signals = {
            "liquidity": {"direction": {"direction": "up"}},
            "svd": {
                "intent": "accumulating",
                "phase": "execution",
                "dom_imbalance": {"side": "ask"}
            },
            "structure": {"trend": "bullish"},
            "ta": {"trend": "bullish"},
            "signal": "BUY"
        }
        
        result = self.detector.detect_conflicts(signals)
        
        assert result["has_conflicts"] == True
        # Должен быть major конфликт
        assert any(c["type"] == "signal_vs_dom" for c in result["conflicts"])

