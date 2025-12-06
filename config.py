"""
Конфигурация проекта SmartMoneyAI v3
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Определяем путь к .env файлу (в корне проекта)
env_path = Path(__file__).parent / '.env'

# Загрузка переменных окружения из .env файла
if env_path.exists():
    # Загружаем с перезаписью существующих переменных
    load_dotenv(dotenv_path=env_path, override=True)
    # Дополнительная проверка - загружаем еще раз из текущей директории
    load_dotenv(override=True)
    print(f"✅ .env файл загружен из: {env_path}")
else:
    print(f"⚠️ .env файл не найден по пути: {env_path}")
    # Пробуем загрузить из текущей директории
    load_dotenv(override=True)


class Config:
    """Класс для хранения всех настроек проекта"""
    
    # ============================================
    # TELEGRAM BOT
    # ============================================
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_ADMIN_ID: Optional[str] = os.getenv("TELEGRAM_ADMIN_ID")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_ADMIN_ID")
    
    # ============================================
    # EXCHANGE
    # ============================================
    EXCHANGE: str = os.getenv("EXCHANGE", "BINGX")
    
    # ============================================
    # BINGX API
    # ============================================
    BINGX_API_KEY: Optional[str] = os.getenv("BINGX_API_KEY")
    BINGX_API_SECRET: Optional[str] = os.getenv("BINGX_API_SECRET")
    BINGX_SECRET_KEY: Optional[str] = os.getenv("BINGX_API_SECRET")  # Алиас для совместимости
    BINGX_BASE_URL: str = "https://open-api.bingx.com"
    
    # ============================================
    # AI НАСТРОЙКИ
    # ============================================
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    AI_MODELS: str = os.getenv("AI_MODELS", "meituan/longcat-flash-chat:free")
    
    # ============================================
    # DATABASE
    # ============================================
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///smart_money_bot.db")
    
    # ============================================
    # ТОРГОВЫЕ НАСТРОЙКИ
    # ============================================
    DEFAULT_SYMBOLS: str = os.getenv("DEFAULT_SYMBOLS", "BTCUSDT")
    SYMBOL: str = DEFAULT_SYMBOLS.replace("USDT", "-USDT") if "USDT" in DEFAULT_SYMBOLS else DEFAULT_SYMBOLS
    UPDATE_INTERVAL: int = int(os.getenv("UPDATE_INTERVAL", "180"))
    ANALYSIS_INTERVAL: int = UPDATE_INTERVAL  # Алиас для совместимости
    
    # Таймфреймы
    KLINE_INTERVAL_YEARLY: str = os.getenv("KLINE_INTERVAL_YEARLY", "1D")
    KLINE_LIMIT_YEARLY: int = int(os.getenv("KLINE_LIMIT_YEARLY", "100"))
    
    KLINE_INTERVAL_LONG: str = os.getenv("KLINE_INTERVAL_LONG", "4h")
    KLINE_LIMIT_LONG: int = int(os.getenv("KLINE_LIMIT_LONG", "100"))
    
    KLINE_INTERVAL: str = os.getenv("KLINE_INTERVAL", "15m")
    KLINE_LIMIT: int = int(os.getenv("KLINE_LIMIT", "100"))
    TIMEFRAME: str = KLINE_INTERVAL  # Алиас для совместимости
    
    MIN_VOLUME_THRESHOLD: float = float(os.getenv("MIN_VOLUME_THRESHOLD", "1000000"))
    MIN_LIQUIDITY_ZONE_SIZE: float = float(os.getenv("MIN_LIQUIDITY_ZONE_SIZE", "50000"))
    
    # ============================================
    # ФИЛЬТРЫ СИГНАЛОВ
    # ============================================
    ENABLE_EMA_FILTER: bool = os.getenv("ENABLE_EMA_FILTER", "True").lower() == "true"
    ENABLE_MACD_FILTER: bool = os.getenv("ENABLE_MACD_FILTER", "True").lower() == "true"
    ENABLE_RSI_FILTER: bool = os.getenv("ENABLE_RSI_FILTER", "True").lower() == "true"
    ENABLE_VOLUME_FILTER: bool = os.getenv("ENABLE_VOLUME_FILTER", "True").lower() == "true"
    # Требовать фазу execution для сигналов (усиление уверенности, меньше шумов)
    EXECUTION_ONLY_SIGNALS: bool = os.getenv("EXECUTION_ONLY_SIGNALS", "False").lower() == "true"
    
    # ============================================
    # HIGHER TIMEFRAME (HTF) ДЛЯ BIAS
    # ============================================
    HTF_1_INTERVAL: str = os.getenv("HTF_1_INTERVAL", "1h")
    HTF_2_INTERVAL: str = os.getenv("HTF_2_INTERVAL", "4h")
    HTF_LIMIT: int = int(os.getenv("HTF_LIMIT", "200"))
    
    # ============================================
    # TRADINGVIEW WEBHOOK
    # ============================================
    ENABLE_TRADINGVIEW_WEBHOOK: bool = os.getenv("ENABLE_TRADINGVIEW_WEBHOOK", "False").lower() == "true"
    
    # ============================================
    # ЕЖЕДНЕВНЫЙ ОТЧЕТ
    # ============================================
    ENABLE_DAILY_REPORT: bool = os.getenv("ENABLE_DAILY_REPORT", "True").lower() == "true"
    DAILY_REPORT_HOUR: int = int(os.getenv("DAILY_REPORT_HOUR", "5"))
    DAILY_REPORT_MINUTE: int = int(os.getenv("DAILY_REPORT_MINUTE", "0"))
    
    # ============================================
    # ПУТИ
    # ============================================
    DATA_DIR: str = "data"
    CACHE_DIR: str = "data/cache"
    SAMPLES_DIR: str = "data/samples"
    LOGS_DIR: str = "logs"
    
    # ============================================
    # НАСТРОЙКИ МОДУЛЕЙ
    # ============================================
    LIQUIDITY_LOOKBACK: int = 100  # свечей для анализа ликвидности
    SVD_WINDOW: int = 20  # окно для SVD анализа
    MIN_CONFIDENCE: float = 7.0  # минимальный confidence для сигнала

    # ============================================
    # WEBSOCKET НАСТРОЙКИ
    # ============================================
    WS_ENABLED: bool = os.getenv("WS_ENABLED", "True").lower() == "true"
    WS_BASE_URL: str = os.getenv("WS_BASE_URL", "wss://open-api-swap.bingx.com/swap-market")
    WS_DEPTH_LEVEL: int = int(os.getenv("WS_DEPTH_LEVEL", "20"))
    WS_TRADES_BUFFER: int = int(os.getenv("WS_TRADES_BUFFER", "1000"))
    
    def __init__(self):
        """Инициализация и создание необходимых директорий"""
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        os.makedirs(self.SAMPLES_DIR, exist_ok=True)
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        
        # Data Validation Settings
        self.MAX_AGE_OHLCV_SECONDS = int(os.getenv('MAX_AGE_OHLCV_SECONDS', '300'))
        self.MAX_AGE_ORDERBOOK_SECONDS = int(os.getenv('MAX_AGE_ORDERBOOK_SECONDS', '10'))
        self.MAX_AGE_TRADES_SECONDS = int(os.getenv('MAX_AGE_TRADES_SECONDS', '30'))
        self.MIN_ORDERBOOK_LEVELS = int(os.getenv('MIN_ORDERBOOK_LEVELS', '10'))
        self.MIN_TRADES_COUNT = int(os.getenv('MIN_TRADES_COUNT', '20'))
        self.MIN_OHLCV_CANDLES = int(os.getenv('MIN_OHLCV_CANDLES', '50'))
        self.MIN_DATA_QUALITY = float(os.getenv('MIN_DATA_QUALITY', '0.5'))  # Минимальный порог quality_score
        
        # Conflict Detection Settings
        self.CRITICAL_CONFLICT_THRESHOLD = int(os.getenv('CRITICAL_CONFLICT_THRESHOLD', '2'))  # Количество критичных конфликтов для force WAIT
        
        # Trap Engine Settings
        self.TRAP_SCORE_THRESHOLD = float(os.getenv('TRAP_SCORE_THRESHOLD', '3.0'))  # Минимальный score для детекции trap
    
    @property
    def analysis_interval(self) -> int:
        """Интервал анализа в секундах"""
        return self.ANALYSIS_INTERVAL
    
    def get_symbol_for_api(self) -> str:
        """Возвращает символ в формате для API (BTC-USDT)"""
        return self.SYMBOL
    
    def get_symbol_for_exchange(self) -> str:
        """Возвращает символ в формате биржи (BTCUSDT)"""
        return self.DEFAULT_SYMBOLS
