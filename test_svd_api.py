"""
Тест API для SVD: проверка получения orderbook и trades от BingX
"""
import asyncio
from api.data_feed import DataFeed
from config import Config
from modules.svd.svd_engine import SVDEngine

async def test_svd_api():
    """Тестирование получения данных для SVD"""
    print("=" * 60)
    print("🧪 ТЕСТ API ДЛЯ SVD ENGINE")
    print("=" * 60)
    
    # Инициализация
    config = Config()
    data_feed = DataFeed(config)
    svd_engine = SVDEngine()
    
    print(f"\n📊 Конфигурация:")
    print(f"   Symbol: {config.SYMBOL}")
    print(f"   API Key: {'✅ SET' if config.BINGX_API_KEY else '❌ NOT SET'}")
    print(f"   API Secret: {'✅ SET' if config.BINGX_API_SECRET else '❌ NOT SET'}")
    
    # 1. Тест получения orderbook
    print(f"\n{'=' * 60}")
    print("1️⃣ ТЕСТ: Получение Orderbook (стакан заявок)")
    print("=" * 60)
    
    try:
        orderbook = await data_feed.get_orderbook(limit=20)
        
        if orderbook:
            print(f"✅ Orderbook получен успешно!")
            print(f"   Тип: {type(orderbook)}")
            print(f"   Ключи: {list(orderbook.keys())}")
            
            if "bids" in orderbook:
                bids = orderbook["bids"]
                print(f"   📉 Bids (заявки на покупку): {len(bids)} уровней")
                if bids:
                    print(f"      Лучший bid: ${bids[0][0]:.2f} (объем: {bids[0][1]:.4f})")
                    print(f"      Последний bid: ${bids[-1][0]:.2f} (объем: {bids[-1][1]:.4f})")
            
            if "asks" in orderbook:
                asks = orderbook["asks"]
                print(f"   📈 Asks (заявки на продажу): {len(asks)} уровней")
                if asks:
                    print(f"      Лучший ask: ${asks[0][0]:.2f} (объем: {asks[0][1]:.4f})")
                    print(f"      Последний ask: ${asks[-1][0]:.2f} (объем: {asks[-1][1]:.4f})")
            
            if "avg_bid" in orderbook:
                print(f"   📊 Средний объем bid: {orderbook['avg_bid']:.4f}")
            if "avg_ask" in orderbook:
                print(f"   📊 Средний объем ask: {orderbook['avg_ask']:.4f}")
        else:
            print(f"❌ Ошибка: Orderbook не получен (пустой результат)")
            
    except Exception as e:
        print(f"❌ Ошибка при получении orderbook: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Тест получения trades
    print(f"\n{'=' * 60}")
    print("2️⃣ ТЕСТ: Получение Trades (поток сделок)")
    print("=" * 60)
    
    try:
        trades = await data_feed.get_trades(limit=100)
        
        if trades:
            print(f"✅ Trades получены успешно!")
            print(f"   Тип: {type(trades)}")
            print(f"   Количество сделок: {len(trades)}")
            
            if len(trades) > 0:
                print(f"\n   📋 Примеры сделок (первые 5):")
                for i, trade in enumerate(trades[:5]):
                    if isinstance(trade, dict):
                        print(f"      {i+1}. Цена: ${trade.get('price', 0):.2f}, "
                              f"Объем: {trade.get('volume', 0):.4f}, "
                              f"Сторона: {trade.get('side', 'unknown')}, "
                              f"Время: {trade.get('timestamp', 0)}")
                    else:
                        print(f"      {i+1}. {trade}")
                
                # Статистика
                buy_trades = [t for t in trades if isinstance(t, dict) and t.get('side') == 'buy']
                sell_trades = [t for t in trades if isinstance(t, dict) and t.get('side') == 'sell']
                print(f"\n   📊 Статистика:")
                print(f"      Покупки (buy): {len(buy_trades)}")
                print(f"      Продажи (sell): {len(sell_trades)}")
                
                if buy_trades:
                    buy_volume = sum(t.get('volume', 0) for t in buy_trades)
                    print(f"      Общий объем покупок: {buy_volume:.4f}")
                
                if sell_trades:
                    sell_volume = sum(t.get('volume', 0) for t in sell_trades)
                    print(f"      Общий объем продаж: {sell_volume:.4f}")
        else:
            print(f"❌ Ошибка: Trades не получены (пустой результат)")
            
    except Exception as e:
        print(f"❌ Ошибка при получении trades: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Тест SVD Engine с реальными данными
    print(f"\n{'=' * 60}")
    print("3️⃣ ТЕСТ: Обработка данных в SVD Engine")
    print("=" * 60)
    
    try:
        # Получаем данные заново для теста
        orderbook = await data_feed.get_orderbook(limit=20)
        trades = await data_feed.get_trades(limit=100)
        
        if orderbook and trades:
            print(f"✅ Данные получены для SVD анализа")
            print(f"   Orderbook: {'✅' if orderbook else '❌'}")
            print(f"   Trades: {len(trades) if trades else 0} сделок")
            
            # Запускаем SVD анализ
            svd_result = svd_engine.analyze(trades, orderbook)
            
            print(f"\n📊 Результаты SVD анализа:")
            print(f"   Дельта (Delta): {svd_result.get('delta', 0):.2f}")
            print(f"   Намерение (Intent): {svd_result.get('intent', 'unknown')}")
            print(f"   Уверенность (Confidence): {svd_result.get('confidence', 0):.1f}/10")
            
            absorption = svd_result.get('absorption', {})
            print(f"   Поглощение (Absorption): {'✅ Да' if absorption.get('absorbing') else '❌ Нет'}")
            if absorption.get('absorbing'):
                print(f"      Сторона: {absorption.get('side', 'unknown')}")
            
            aggression = svd_result.get('aggression', {})
            print(f"   Агрессия покупок: {aggression.get('buy_aggression', 0):.2f}")
            print(f"   Агрессия продаж: {aggression.get('sell_aggression', 0):.2f}")
            
            velocity = svd_result.get('velocity', {})
            print(f"   Скорость сделок: {velocity.get('velocity', 0):.2f} сделок/сек")
            
            print(f"\n✅ SVD Engine работает корректно!")
        else:
            print(f"❌ Недостаточно данных для SVD анализа")
            print(f"   Orderbook: {'✅' if orderbook else '❌'}")
            print(f"   Trades: {'✅' if trades else '❌'}")
            
    except Exception as e:
        print(f"❌ Ошибка при обработке данных в SVD Engine: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Итоговый вывод
    print(f"\n{'=' * 60}")
    print("📋 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    # Финальная проверка
    try:
        all_data = await data_feed.get_latest_data()
        
        has_ohlcv = not all_data.get("ohlcv", pd.DataFrame()).empty
        has_orderbook = bool(all_data.get("orderbook"))
        has_trades = len(all_data.get("trades", [])) > 0
        
        print(f"\n✅ OHLCV данные: {'✅' if has_ohlcv else '❌'}")
        print(f"✅ Orderbook данные: {'✅' if has_orderbook else '❌'}")
        print(f"✅ Trades данные: {'✅' if has_trades else '❌'}")
        
        if has_ohlcv and has_orderbook and has_trades:
            print(f"\n🎉 ВСЕ ДАННЫЕ ПОЛУЧЕНЫ УСПЕШНО!")
            print(f"   SVD Engine может работать с полными данными")
        else:
            print(f"\n⚠️ НЕКОТОРЫЕ ДАННЫЕ ОТСУТСТВУЮТ")
            if not has_orderbook:
                print(f"   ❌ Orderbook не получен - SVD не сможет анализировать поглощение")
            if not has_trades:
                print(f"   ❌ Trades не получены - SVD не сможет анализировать дельту и агрессию")
                
    except Exception as e:
        print(f"❌ Ошибка при финальной проверке: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'=' * 60}")

if __name__ == "__main__":
    import pandas as pd
    asyncio.run(test_svd_api())

