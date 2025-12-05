# api/websocket_manager.py

import asyncio
import websockets
import json
import logging
from collections import deque

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Менеджер WebSocket подключений для получения данных в реальном времени

    Потоки:
      - trades: market.trade.detail
      - depth: market.depth (level: 5/20)
    Данные хранятся в буферах:
      - self.trades: deque[{price, volume, side, timestamp}]
      - self.orderbook: dict {bids, asks, avg_bid, avg_ask}
    """

    def __init__(self, config):
        self.config = config
        # Рекомендованный домен для swap WS
        self.ws_url = getattr(config, "WS_BASE_URL", "wss://open-api-swap.bingx.com/swap-market")
        self.symbol = config.get_symbol_for_api() if hasattr(config, "get_symbol_for_api") else getattr(config, "SYMBOL", "BTC-USDT")
        self.depth_level = getattr(config, "WS_DEPTH_LEVEL", 20)
        self.enabled = getattr(config, "WS_ENABLED", True)

        # Буферы
        self.trades = deque(maxlen=getattr(config, "WS_TRADES_BUFFER", 1000))
        self.orderbook = {}

        # Таски
        self._tasks = []
        self._running = False

    async def start(self):
        """Запуск WebSocket потоков"""
        if not self.enabled:
            logger.info("WS отключен (WS_ENABLED=false)")
            return
        if self._running:
            return
        self._running = True
        logger.info(f"WebSocket менеджер запущен: {self.ws_url}, symbol={self.symbol}")
        self._tasks = [
            asyncio.create_task(self._run_trades()),
            asyncio.create_task(self._run_depth())
        ]

    async def stop(self):
        """Остановка WebSocket потоков"""
        self._running = False
        for t in self._tasks:
            t.cancel()
        self._tasks = []
        logger.info("WebSocket менеджер остановлен")

    # ------------------ Публичные снимки ------------------ #
    def get_trades_snapshot(self):
        """Возвращает копию буфера trades"""
        return list(self.trades)

    def get_orderbook_snapshot(self):
        """Возвращает последний стакан"""
        return self.orderbook.copy() if self.orderbook else {}

    # ------------------ Внутренние потоки ------------------ #
    async def _run_trades(self):
        """Подписка на trades"""
        backoff = [1, 2, 5, 15, 30]
        idx = 0
        while self._running:
            try:
                async with websockets.connect(self.ws_url, ping_interval=None) as ws:
                    logger.info("WS trades connected")
                    sub_msg = {
                        "id": "trades-1",
                        "reqType": "sub",
                        "dataType": "market.trade.detail",
                        "data": {"symbol": self.symbol}
                    }
                    await ws.send(json.dumps(sub_msg))
                    idx = 0
                    async for raw in ws:
                        if raw is None:
                            continue
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8")
                        msg = json.loads(raw)
                        # Ping/Pong
                        if isinstance(msg, dict) and "ping" in msg:
                            await ws.send(json.dumps({"pong": msg["ping"]}))
                            continue
                        data = msg.get("data")
                        if not data:
                            continue
                        # Список сделок
                        if isinstance(data, list):
                            for t in data:
                                price = float(t.get("p", t.get("price", 0)) or 0)
                                vol = float(t.get("v", t.get("qty", 0)) or 0)
                                side = t.get("S", t.get("side", ""))
                                if side in (True, False):
                                    side = "sell" if side else "buy"
                                elif side == "BUY":
                                    side = "buy"
                                elif side == "SELL":
                                    side = "sell"
                                ts = t.get("T", t.get("timestamp", t.get("time", 0)))
                                self.trades.append({
                                    "price": price,
                                    "volume": vol,
                                    "side": side,
                                    "timestamp": ts
                                })
                        elif isinstance(data, dict):
                            price = float(data.get("p", data.get("price", 0)) or 0)
                            vol = float(data.get("v", data.get("qty", 0)) or 0)
                            side = data.get("S", data.get("side", ""))
                            if side in (True, False):
                                side = "sell" if side else "buy"
                            elif side == "BUY":
                                side = "buy"
                            elif side == "SELL":
                                side = "sell"
                            ts = data.get("T", data.get("timestamp", data.get("time", 0)))
                            self.trades.append({
                                "price": price,
                                "volume": vol,
                                "side": side,
                                "timestamp": ts
                            })
            except asyncio.CancelledError:
                break
            except Exception as e:
                wait = backoff[min(idx, len(backoff) - 1)]
                idx += 1
                logger.warning(f"WS trades reconnect in {wait}s after error: {e}")
                await asyncio.sleep(wait)

    async def _run_depth(self):
        """Подписка на стакан (depth)"""
        backoff = [1, 2, 5, 15, 30]
        idx = 0
        while self._running:
            try:
                async with websockets.connect(self.ws_url, ping_interval=None) as ws:
                    logger.info("WS depth connected")
                    sub_msg = {
                        "id": "depth-1",
                        "reqType": "sub",
                        "dataType": "market.depth",
                        "data": {"symbol": self.symbol, "level": self.depth_level}
                    }
                    await ws.send(json.dumps(sub_msg))
                    idx = 0
                    async for raw in ws:
                        if raw is None:
                            continue
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8")
                        msg = json.loads(raw)
                        if isinstance(msg, dict) and "ping" in msg:
                            await ws.send(json.dumps({"pong": msg["ping"]}))
                            continue
                        data = msg.get("data")
                        if not data:
                            continue
                        bids = data.get("bids", [])
                        asks = data.get("asks", [])
                        if bids or asks:
                            avg_bid = sum(float(b[1]) for b in bids) / len(bids) if bids else 0
                            avg_ask = sum(float(a[1]) for a in asks) / len(asks) if asks else 0
                            self.orderbook = {
                                "bids": [(float(b[0]), float(b[1])) for b in bids],
                                "asks": [(float(a[0]), float(a[1])) for a in asks],
                                "avg_bid": avg_bid,
                                "avg_ask": avg_ask
                            }
            except asyncio.CancelledError:
                break
            except Exception as e:
                wait = backoff[min(idx, len(backoff) - 1)]
                idx += 1
                logger.warning(f"WS depth reconnect in {wait}s after error: {e}")
                await asyncio.sleep(wait)

