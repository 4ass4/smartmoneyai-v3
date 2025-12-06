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
from modules.utils.data_validator import DataQualityValidator
from modules.utils.healthcheck import HealthMonitor
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
    ws_manager = WebSocketManager(config)
    data_feed = DataFeed(config, ws_manager=ws_manager)
    notification_manager = NotificationManager(config)
    data_validator = DataQualityValidator(config)
    health_monitor = HealthMonitor()
    
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
                ta_engine,
                health_monitor=health_monitor
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
            async def health_wrapper(update, context: ContextTypes.DEFAULT_TYPE):
                await handlers.handle_health(update, context)
            
            application.add_handler(CommandHandler("start", start_wrapper))
            application.add_handler(CommandHandler("status", status_wrapper))
            application.add_handler(CommandHandler("signal", signal_wrapper))
            application.add_handler(CommandHandler("analysis", analysis_wrapper))
            application.add_handler(CommandHandler("health", health_wrapper))
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
            fetch_timestamp = data_feed.get_fetch_timestamp()
            
            if market_data["ohlcv"].empty:
                logger.warning("Нет данных OHLCV")
                await asyncio.sleep(config.analysis_interval)
                continue
            
            # Валидация качества данных
            validation_result = data_validator.validate_all(
                market_data["ohlcv"],
                market_data.get("orderbook"),
                market_data.get("trades"),
                fetch_timestamp
            )
            
            # Логируем качество данных
            overall_quality = validation_result["overall_quality"]
            logger.info(f"📈 Качество данных: {overall_quality:.2f}/1.0")
            
            # Если качество слишком низкое — пропускаем анализ
            if overall_quality < config.MIN_DATA_QUALITY:
                logger.warning(f"⚠️ Качество данных ниже порога ({overall_quality:.2f} < {config.MIN_DATA_QUALITY}), пропускаем итерацию")
                logger.warning(f"   OHLCV: {validation_result['ohlcv']['quality_score']:.2f}, Orderbook: {validation_result['orderbook']['quality_score']:.2f}, Trades: {validation_result['trades']['quality_score']:.2f}")
                await asyncio.sleep(config.analysis_interval)
                continue
            
            # Анализ через модули: Liquidity → SVD → Structure → TA → Decision
            try:
                # 1. Market Structure
                structure_data = market_structure_engine.analyze(market_data["ohlcv"])
                # HTF bias (1h/4h по умолчанию)
                htf1_df = await data_feed.get_ohlcv_tf(config.HTF_1_INTERVAL)
                htf2_df = await data_feed.get_ohlcv_tf(config.HTF_2_INTERVAL)
                htf1_struct = market_structure_engine.analyze(htf1_df) if not htf1_df.empty else {"trend": "unknown"}
                htf2_struct = market_structure_engine.analyze(htf2_df) if not htf2_df.empty else {"trend": "unknown"}
                # HTF liquidity
                htf1_liq = liquidity_engine.analyze(htf1_df, htf1_struct) if not htf1_df.empty else {}
                htf2_liq = liquidity_engine.analyze(htf2_df, htf2_struct) if not htf2_df.empty else {}
                
                # 2. TA (сначала, чтобы получить ATR для нормировки)
                ta_data = ta_engine.analyze(market_data["ohlcv"])
                atr_pct = ta_data.get("atr_pct", None)
                
                # 3. Liquidity
                liquidity_data = liquidity_engine.analyze(market_data["ohlcv"], structure_data)
                
                # 4. SVD (требует trades, orderbook и ATR для нормировки)
                if market_data.get("trades") and market_data.get("orderbook"):
                    svd_data = svd_engine.analyze(market_data["trades"], market_data["orderbook"], atr_pct=atr_pct)
                else:
                    svd_data = {"intent": "unclear", "confidence": 0}
                
                # 5. Decision (передаем текущую цену, HTF контекст и качество данных)
                current_price = market_data["ohlcv"]["close"].iloc[-1]
                signal = decision_engine.analyze(
                    liquidity_data,
                    svd_data,
                    structure_data,
                    ta_data,
                    current_price=current_price,
                    htf_context={
                        "htf1": htf1_struct.get("trend", "unknown"),
                        "htf2": htf2_struct.get("trend", "unknown"),
                    },
                    htf_liquidity={
                        "htf1": htf1_liq.get("direction", {}) if htf1_liq else {},
                        "htf2": htf2_liq.get("direction", {}) if htf2_liq else {},
                    },
                    data_quality=validation_result
                )
                
                # Добавляем текущую цену в signals для расчета уровней
                # (временное решение, лучше передавать в analyze)
                if "current_price" not in signal:
                    signal["current_price"] = current_price
                
                # Сохранение последнего сигнала для handlers
                if handlers:
                    handlers.set_last_signal(signal)
                
                # Логирование всех сигналов для отладки
                signal_type = signal.get("signal", "UNKNOWN")
                confidence = signal.get("confidence", 0)
                logger.info(f"📊 Сгенерирован сигнал: {signal_type} (confidence: {confidence:.1f}/10)")
                
                # Записываем в healthcheck
                health_monitor.record_signal(signal_type)
                
                # Отправка сигнала в Telegram с детальными данными
                if signal and signal.get("signal") != "WAIT":
                    logger.info(f"✅ Сигнал {signal_type} не WAIT, отправляем...")
                    try:
                        await notification_manager.send_signal(
                            signal,
                            structure_data=structure_data,
                            liquidity_data=liquidity_data,
                            svd_data=svd_data,
                            ta_data=ta_data,
                            current_price=market_data["ohlcv"]["close"].iloc[-1]
                        )
                        logger.info(f"✅ Сигнал {signal_type} успешно отправлен в Telegram")
                    except Exception as e:
                        logger.error(f"❌ Ошибка отправки сигнала: {e}", exc_info=True)
                        health_monitor.record_error()
                else:
                    logger.debug(f"⏸️ Сигнал WAIT или отсутствует, пропускаем отправку")
                
                # Периодически логируем статус (каждые 10 итераций или 30 минут)
                if health_monitor.signal_count % 10 == 0 or health_monitor.uptime_seconds() % 1800 < config.analysis_interval:
                    health_monitor.log_status()
                
            except Exception as e:
                logger.error(f"Ошибка анализа: {e}", exc_info=True)
                health_monitor.record_error()
            
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

