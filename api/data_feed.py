# api/data_feed.py

import pandas as pd
from .bingx_client import BingXClient


class DataFeed:
    """
    Унифицированный загрузчик данных для модулей
    """

    def __init__(self, config, ws_manager=None):
        self.config = config
        self.ws_manager = ws_manager
        # Поддержка обоих вариантов названия secret key
        secret_key = getattr(config, 'BINGX_API_SECRET', None) or getattr(config, 'BINGX_SECRET_KEY', None)
        self.client = BingXClient(
            api_key=getattr(config, 'BINGX_API_KEY', None),
            secret_key=secret_key
        )
        # Получаем символ в правильном формате
        self.symbol = config.get_symbol_for_api() if hasattr(config, 'get_symbol_for_api') else getattr(config, 'SYMBOL', 'BTC-USDT')
        self.timeframe = getattr(config, 'TIMEFRAME', '15m')

    def _get_klines(self, symbol, interval, limit):
        klines = self.client.get_klines(symbol, interval, limit)
        if not klines:
            return pd.DataFrame()
        data = None
        if isinstance(klines, dict):
            if klines.get('code') == 0 and 'data' in klines:
                data = klines['data']
            elif 'data' in klines:
                data = klines['data']
            else:
                return pd.DataFrame()
        elif isinstance(klines, list):
            data = klines
        else:
            return pd.DataFrame()
        if not data or len(data) == 0:
            return pd.DataFrame()
        if isinstance(data[0], dict):
            df = pd.DataFrame(data).rename(columns={'time': 'timestamp'})
            df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.sort_values('timestamp').reset_index(drop=True)
        else:
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = df.astype({
            'timestamp': 'int64',
            'open': 'float64',
            'high': 'float64',
            'low': 'float64',
            'close': 'float64',
            'volume': 'float64'
        })
        return df

    async def get_ohlcv(self, limit=None):
        """
        Получение OHLCV данных
        
        Args:
            limit: количество свечей (по умолчанию из config)
            
        Returns:
            DataFrame с OHLCV данными
        """
        if limit is None:
            limit = getattr(self.config, 'KLINE_LIMIT', 100)
        return self._get_klines(self.symbol, self.timeframe, limit)

    async def get_ohlcv_tf(self, interval: str, limit=None):
        """
        OHLCV для другого таймфрейма (HTF)
        """
        if limit is None:
            limit = getattr(self.config, 'HTF_LIMIT', 200)
        return self._get_klines(self.symbol, interval, limit)

    async def get_orderbook(self, limit=20):
        """
        Получение стакана заявок
        
        Args:
            limit: глубина стакана
            
        Returns:
            Dict со стаканом в формате для модулей
        """
        # Сначала пробуем взять из WebSocket, если доступен
        if self.ws_manager:
            ob = self.ws_manager.get_orderbook_snapshot()
            if ob:
                return ob

        result = self.client.get_orderbook(self.symbol, limit)
        
        if not result:
            return {}
        
        # Обработка формата BingX
        if isinstance(result, dict):
            if result.get('code') == 0 and 'data' in result:
                data = result['data']
                # Преобразуем в нужный формат
                bids = data.get('bids', [])
                asks = data.get('asks', [])
                
                # Вычисляем средние значения
                avg_bid = sum(float(b[1]) for b in bids) / len(bids) if bids else 0
                avg_ask = sum(float(a[1]) for a in asks) / len(asks) if asks else 0
                
                return {
                    "bids": [(float(b[0]), float(b[1])) for b in bids],
                    "asks": [(float(a[0]), float(a[1])) for a in asks],
                    "avg_bid": avg_bid,
                    "avg_ask": avg_ask
                }
        
        return {}

    async def get_trades(self, limit=100):
        """
        Получение последних сделок
        
        Args:
            limit: количество сделок
            
        Returns:
            List сделок в формате для SVD модуля
        """
        # Сначала пробуем взять из WebSocket, если доступен
        if self.ws_manager:
            trades = self.ws_manager.get_trades_snapshot()
            if trades:
                return trades

        result = self.client.get_trades(self.symbol, limit)
        
        if not result:
            return []
        
        # Обработка формата BingX
        if isinstance(result, dict):
            if result.get('code') == 0 and 'data' in result:
                data = result['data']
                # Преобразуем в нужный формат для SVD
                trades = []
                for trade in data:
                    if isinstance(trade, dict):
                        # BingX формат: {"price": "...", "qty": "...", "time": ..., "isBuyerMaker": true/false}
                        trades.append({
                            "price": float(trade.get('price', 0)),
                            "volume": float(trade.get('qty', 0)),
                            "side": "sell" if trade.get('isBuyerMaker', False) else "buy",
                            "timestamp": trade.get('time', 0)
                        })
                    elif isinstance(trade, list):
                        # Старый формат (список)
                        trades.append({
                            "price": float(trade[0]) if len(trade) > 0 else 0,
                            "volume": float(trade[1]) if len(trade) > 1 else 0,
                            "side": "buy" if len(trade) > 2 and trade[2] else "sell",
                            "timestamp": trade[3] if len(trade) > 3 else 0
                        })
                return trades
            elif isinstance(result, list):
                # Если результат уже список
                return result
        
        return []

    async def get_latest_data(self):
        """
        Получение всех последних данных
        
        Returns:
            Dict со всеми данными
        """
        return {
            "ohlcv": await self.get_ohlcv(),
            "orderbook": await self.get_orderbook(),
            "trades": await self.get_trades()
        }

