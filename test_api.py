"""
Тест BingX API
"""
from api.bingx_client import BingXClient
from config import Config

c = Config()
print(f"API Key: {'SET' if c.BINGX_API_KEY else 'NOT SET'}")
print(f"Symbol: {c.SYMBOL}")
print(f"Timeframe: {c.TIMEFRAME}")

client = BingXClient(c.BINGX_API_KEY, c.BINGX_API_SECRET)
print(f"\nТестирую запрос к BingX API...")
print(f"URL: {client.base_url}")
print(f"Symbol: {c.SYMBOL}, Interval: {c.TIMEFRAME}, Limit: 10")

result = client.get_klines(c.SYMBOL, c.TIMEFRAME, 10)

if result:
    print(f"\n✅ Ответ получен!")
    print(f"Тип: {type(result)}")
    if isinstance(result, dict):
        print(f"Ключи: {list(result.keys())}")
        if 'code' in result:
            print(f"Code: {result.get('code')}")
        if 'msg' in result:
            print(f"Message: {result.get('msg')}")
        if 'data' in result:
            data = result['data']
            print(f"Data type: {type(data)}")
            if isinstance(data, list) and len(data) > 0:
                print(f"Количество свечей: {len(data)}")
                print(f"Первая свеча: {data[0]}")
    elif isinstance(result, list):
        print(f"Количество свечей: {len(result)}")
        if len(result) > 0:
            print(f"Первая свеча: {result[0]}")
else:
    print(f"\n❌ Ошибка: результат None")

