# api/bingx_client.py

import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode


class BingXClient:
    """
    Клиент для работы с BingX API (REST)
    """

    def __init__(self, api_key=None, secret_key=None, base_url="https://open-api.bingx.com"):
        self.api_key = api_key
        self.secret_key = secret_key or secret_key  # Поддержка обоих вариантов
        self.base_url = base_url

    def _generate_signature(self, params):
        """Генерация подписи для запроса"""
        if not self.secret_key:
            return ""
        query_string = urlencode(sorted(params.items()))
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def get_klines(self, symbol, interval, limit=500):
        """
        Получение свечных данных
        
        Args:
            symbol: символ (например, BTC-USDT)
            interval: интервал (1m, 5m, 1h, etc.)
            limit: количество свечей
            
        Returns:
            List свечей
        """
        # Правильный endpoint для BingX Swap API
        # Символ должен быть с дефисом: BTC-USDT
        endpoint = "/openApi/swap/v2/quote/klines"
        params = {
            "symbol": symbol,  # Оставляем с дефисом: BTC-USDT
            "interval": interval,
            "limit": limit
        }
        
        url = f"{self.base_url}{endpoint}?{urlencode(params)}"
        response = requests.get(url)
        
        # Логирование для отладки
        if response.status_code != 200:
            print(f"API Error: {response.status_code} - {response.text[:200]}")
        else:
            result = response.json()
            if isinstance(result, dict) and result.get('code') != 0:
                print(f"API Error Code: {result.get('code')} - {result.get('msg', 'Unknown error')}")
        
        if response.status_code == 200:
            return response.json()
        return None

    def get_orderbook(self, symbol, limit=20):
        """
        Получение стакана заявок
        
        Args:
            symbol: символ
            limit: глубина стакана
            
        Returns:
            Dict со стаканом
        """
        endpoint = "/openApi/swap/v2/quote/depth"
        params = {
            "symbol": symbol,
            "limit": limit
        }
        
        url = f"{self.base_url}{endpoint}?{urlencode(params)}"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        return None

    def get_trades(self, symbol, limit=100):
        """
        Получение последних сделок
        
        Args:
            symbol: символ
            limit: количество сделок
            
        Returns:
            List сделок
        """
        endpoint = "/openApi/swap/v2/quote/trades"
        params = {
            "symbol": symbol,
            "limit": limit
        }
        
        url = f"{self.base_url}{endpoint}?{urlencode(params)}"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        return None

