"""
Комплексный тест анализа рынка по логике SmartMoneyAI v3
Проверяет работу всех модулей: Liquidity → SVD → Structure → TA → Decision
"""

import asyncio
import pandas as pd
from config import Config
from api.data_feed import DataFeed
from modules.liquidity.liquidity_engine import LiquidityEngine
from modules.svd.svd_engine import SVDEngine
from modules.market_structure.market_structure_engine import MarketStructureEngine
from modules.ta_engine.ta_engine import TAEngine
from modules.decision.decision_engine import DecisionEngine

async def test_full_analysis():
    """Полный тест анализа рынка"""
    print("=" * 60)
    print("🧪 ТЕСТ АНАЛИЗА РЫНКА SmartMoneyAI v3")
    print("=" * 60)
    
    # Инициализация
    config = Config()
    data_feed = DataFeed(config)
    
    print("\n📊 ШАГ 1: Получение данных с BingX...")
    market_data = await data_feed.get_latest_data()
    
    # Проверка данных
    if market_data["ohlcv"].empty:
        print("❌ ОШИБКА: Нет данных OHLCV")
        return
    
    print(f"✅ OHLCV данные получены: {len(market_data['ohlcv'])} свечей")
    print(f"   Последняя цена: {market_data['ohlcv']['close'].iloc[-1]:.2f}")
    print(f"   Период: {market_data['ohlcv']['timestamp'].iloc[0]} - {market_data['ohlcv']['timestamp'].iloc[-1]}")
    
    # Проверка trades и orderbook
    trades_count = len(market_data.get("trades", []))
    orderbook_available = bool(market_data.get("orderbook"))
    print(f"✅ Trades: {trades_count} сделок")
    print(f"✅ Orderbook: {'Доступен' if orderbook_available else 'Недоступен'}")
    
    print("\n" + "=" * 60)
    print("📈 ШАГ 2: Market Structure Analysis")
    print("=" * 60)
    
    market_structure_engine = MarketStructureEngine()
    structure_data = market_structure_engine.analyze(market_data["ohlcv"])
    
    print(f"✅ Тренд: {structure_data.get('trend', 'unknown')}")
    print(f"✅ Swing Highs: {len(structure_data.get('swings', {}).get('highs', []))}")
    print(f"✅ Swing Lows: {len(structure_data.get('swings', {}).get('lows', []))}")
    print(f"✅ FVG: {len(structure_data.get('fvg', []))} gaps")
    print(f"✅ Order Blocks: {len(structure_data.get('orderblocks', []))}")
    if structure_data.get('range', {}).get('in_range'):
        range_info = structure_data['range']
        print(f"✅ Range: {range_info.get('bottom', 0):.2f} - {range_info.get('top', 0):.2f}")
    
    print("\n" + "=" * 60)
    print("💧 ШАГ 3: Liquidity Analysis")
    print("=" * 60)
    
    liquidity_engine = LiquidityEngine()
    liquidity_data = liquidity_engine.analyze(market_data["ohlcv"], structure_data)
    
    direction = liquidity_data.get("direction", {})
    print(f"✅ Направление ликвидности: {direction.get('direction', 'unknown')}")
    print(f"   Причина: {direction.get('reason', 'N/A')}")
    print(f"✅ Stop Clusters: {len(liquidity_data.get('stop_clusters', []))}")
    print(f"✅ Swing Liquidity: {len(liquidity_data.get('swing_liquidity', []))}")
    ath_atl = liquidity_data.get("ath_atl", {})
    if ath_atl:
        print(f"✅ ATH: {ath_atl.get('ath', {}).get('price', 'N/A')}")
        print(f"✅ ATL: {ath_atl.get('atl', {}).get('price', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("📊 ШАГ 4: SVD Analysis (Order Flow)")
    print("=" * 60)
    
    svd_engine = SVDEngine()
    if market_data.get("trades") and market_data.get("orderbook"):
        svd_data = svd_engine.analyze(market_data["trades"], market_data["orderbook"])
        print(f"✅ Дельта: {svd_data.get('delta', 0):.2f}")
        print(f"✅ Intent: {svd_data.get('intent', 'unclear')}")
        print(f"✅ Confidence: {svd_data.get('confidence', 0)}/10")
        absorption = svd_data.get('absorption', {})
        if absorption.get('absorbing'):
            print(f"✅ Поглощение обнаружено: {absorption.get('side', 'unknown')}")
        aggression = svd_data.get('aggression', {})
        print(f"✅ Buy Aggression: {aggression.get('buy_aggression', 0):.2f}")
        print(f"✅ Sell Aggression: {aggression.get('sell_aggression', 0):.2f}")
        velocity = svd_data.get('velocity', {})
        print(f"✅ Trade Velocity: {velocity.get('velocity', 0):.4f}")
    else:
        print("⚠️ SVD анализ пропущен (нет trades/orderbook)")
        svd_data = {"intent": "unclear", "confidence": 0}
    
    print("\n" + "=" * 60)
    print("📉 ШАГ 5: Technical Analysis")
    print("=" * 60)
    
    ta_engine = TAEngine()
    ta_data = ta_engine.analyze(market_data["ohlcv"])
    
    print(f"✅ Trend: {ta_data.get('trend', 'unknown')}")
    print(f"✅ EMA Fast: {ta_data.get('ema_fast', 0):.2f}")
    print(f"✅ EMA Slow: {ta_data.get('ema_slow', 0):.2f}")
    print(f"✅ RSI: {ta_data.get('rsi', 0):.2f}")
    print(f"✅ Overbought: {ta_data.get('overbought', False)}")
    print(f"✅ Oversold: {ta_data.get('oversold', False)}")
    patterns = ta_data.get('patterns', [])
    if patterns:
        print(f"✅ Patterns: {len(patterns)} обнаружено")
        for p in patterns[:3]:
            print(f"   - {p.get('type', 'unknown')} ({p.get('strength', 'unknown')})")
    
    print("\n" + "=" * 60)
    print("🎯 ШАГ 6: Decision Engine (Финальное решение)")
    print("=" * 60)
    
    decision_engine = DecisionEngine(config)
    signal = decision_engine.analyze(
        liquidity_data,
        svd_data,
        structure_data,
        ta_data
    )
    
    print(f"✅ Signal: {signal.get('signal', 'WAIT')}")
    print(f"✅ Confidence: {signal.get('confidence', 0):.1f}/10")
    print(f"✅ Explanation: {signal.get('explanation', 'N/A')}")
    
    scenario = signal.get('scenario', {})
    if scenario:
        print(f"✅ Main Scenario: {scenario.get('main', 'N/A')[:100]}...")
    
    levels = signal.get('levels', {})
    if levels:
        print(f"✅ Entry Zone: {levels.get('entry_zone', 'N/A')}")
        print(f"✅ Targets: {levels.get('targets', [])}")
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
    print("=" * 60)
    
    # Итоговая сводка
    print("\n📋 ИТОГОВАЯ СВОДКА:")
    print(f"   • Market Structure: {structure_data.get('trend', 'unknown')}")
    print(f"   • Liquidity Direction: {direction.get('direction', 'unknown')}")
    print(f"   • SVD Intent: {svd_data.get('intent', 'unclear')}")
    print(f"   • TA Trend: {ta_data.get('trend', 'unknown')}")
    print(f"   • ФИНАЛЬНЫЙ СИГНАЛ: {signal.get('signal', 'WAIT')} (Confidence: {signal.get('confidence', 0):.1f}/10)")
    
    return signal

if __name__ == "__main__":
    asyncio.run(test_full_analysis())

