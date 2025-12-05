"""
SmartMoneyAI v3 - Главная точка входа
Запускает WebSocket подписки, вызывает модули анализа и отправляет сигналы в Telegram
"""

import asyncio
import logging
from config import Config
from api.websocket_manager import WebSocketManager
from api.data_feed import DataFeed
from modules.liquidity.liquidity_engine import LiquidityEngine
from modules.svd.svd_engine import SVDEngine
from modules.market_structure.market_structure_engine import MarketStructureEngine
from modules.ta_engine.ta_engine import TAEngine
from modules.decision.decision_engine import DecisionEngine
from bot.notifications import NotificationManager
from bot.handlers import BotHandlers
from telegram import Bot
from telegram.ext import Application, CommandHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/smartmoney.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска системы"""
    logger.info("🚀 Запуск SmartMoneyAI v3...")
    
    # Инициализация компонентов
    config = Config()
    data_feed = DataFeed(config)
    notification_manager = NotificationManager(config)
    ws_manager = WebSocketManager(config)
    
    # Инициализация Telegram бота
    bot_token = config.TELEGRAM_BOT_TOKEN
    application = None
    handlers = None  # Инициализируем для доступа в основном цикле
    if bot_token:
        try:
            bot = Bot(token=bot_token)
            notification_manager.set_bot(bot)
            
            # Инициализация модулей анализа (для handlers)
            liquidity_engine = LiquidityEngine()
            svd_engine = SVDEngine()
            market_structure_engine = MarketStructureEngine()
            ta_engine = TAEngine()
            decision_engine = DecisionEngine(config)
            
            # Инициализация обработчиков команд
            application = Application.builder().token(bot_token).build()
            handlers = BotHandlers(
                bot, 
                decision_engine,
                data_feed,
                liquidity_engine,
                svd_engine,
                market_structure_engine,
                ta_engine
            )
            
            # Регистрация команд
            from telegram.ext import ContextTypes
            async def start_wrapper(update, context: ContextTypes.DEFAULT_TYPE):
                await handlers.handle_start(update, context)
            async def status_wrapper(update, context: ContextTypes.DEFAULT_TYPE):
                await handlers.handle_status(update, context)
            async def signal_wrapper(update, context: ContextTypes.DEFAULT_TYPE):
                await handlers.handle_signal(update, context)
            async def analysis_wrapper(update, context: ContextTypes.DEFAULT_TYPE):
                await handlers.handle_analysis(update, context)
            async def help_wrapper(update, context: ContextTypes.DEFAULT_TYPE):
                await handlers.handle_help(update, context)
            
            application.add_handler(CommandHandler("start", start_wrapper))
            application.add_handler(CommandHandler("status", status_wrapper))
            application.add_handler(CommandHandler("signal", signal_wrapper))
            application.add_handler(CommandHandler("analysis", analysis_wrapper))
            application.add_handler(CommandHandler("help", help_wrapper))
            
            # Запуск бота в фоне
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            
            logger.info("✅ Telegram бот запущен")
        except Exception as e:
            logger.error(f"Ошибка инициализации Telegram бота: {e}")
            logger.warning("Продолжение работы без Telegram бота")
    else:
        logger.warning("TELEGRAM_BOT_TOKEN не установлен. Бот не будет работать.")
    
    # Инициализация модулей анализа (если бот не запущен, создаем здесь)
    if not bot_token or not application:
        liquidity_engine = LiquidityEngine()
        svd_engine = SVDEngine()
        market_structure_engine = MarketStructureEngine()
        ta_engine = TAEngine()
        decision_engine = DecisionEngine(config)
    
    # Запуск WebSocket подписок
    await ws_manager.start()
    
    # Основной цикл обработки
    try:
        while True:
            # Получение данных
            market_data = await data_feed.get_latest_data()
            
            if market_data["ohlcv"].empty:
                logger.warning("Нет данных OHLCV")
                await asyncio.sleep(config.analysis_interval)
                continue
            
            # Анализ через модули: Liquidity → SVD → Structure → TA → Decision
            try:
                # 1. Market Structure
                structure_data = market_structure_engine.analyze(market_data["ohlcv"])
                
                # 2. Liquidity
                liquidity_data = liquidity_engine.analyze(market_data["ohlcv"], structure_data)
                
                # 3. SVD (требует trades и orderbook)
                if market_data.get("trades") and market_data.get("orderbook"):
                    svd_data = svd_engine.analyze(market_data["trades"], market_data["orderbook"])
                else:
                    svd_data = {"intent": "unclear", "confidence": 0}
                
                # 4. TA
                ta_data = ta_engine.analyze(market_data["ohlcv"])
                
                # 5. Decision (передаем текущую цену)
                current_price = market_data["ohlcv"]["close"].iloc[-1]
                signal = decision_engine.analyze(
                    liquidity_data,
                    svd_data,
                    structure_data,
                    ta_data,
                    current_price=current_price
                )
                
                # Добавляем текущую цену в signals для расчета уровней
                # (временное решение, лучше передавать в analyze)
                if "current_price" not in signal:
                    signal["current_price"] = current_price
                
                # Сохранение последнего сигнала для handlers
                if handlers:
                    handlers.set_last_signal(signal)
                
                # Отправка сигнала в Telegram с детальными данными
                if signal and signal.get("signal") != "WAIT":
                    await notification_manager.send_signal(
                        signal,
                        structure_data=structure_data,
                        liquidity_data=liquidity_data,
                        svd_data=svd_data,
                        ta_data=ta_data,
                        current_price=market_data["ohlcv"]["close"].iloc[-1]
                    )
                    logger.info(f"Сигнал: {signal.get('signal')} (confidence: {signal.get('confidence')})")
                
            except Exception as e:
                logger.error(f"Ошибка анализа: {e}", exc_info=True)
            
            await asyncio.sleep(config.analysis_interval)
            
    except KeyboardInterrupt:
        logger.info("Остановка системы...")
    finally:
        await ws_manager.stop()
        if application:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

