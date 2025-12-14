# bot/handlers.py

import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class BotHandlers:
    """
    Обработчики команд Telegram бота
    """

    def __init__(self, bot, decision_engine, data_feed, liquidity_engine, 
                 svd_engine, market_structure_engine, ta_engine, health_monitor=None,
                 historical_phase_analyzer=None, global_trend_analyzer=None):
        self.bot = bot
        self.decision_engine = decision_engine
        self.data_feed = data_feed
        self.liquidity_engine = liquidity_engine
        self.svd_engine = svd_engine
        self.market_structure_engine = market_structure_engine
        self.ta_engine = ta_engine
        self.health_monitor = health_monitor
        self.historical_phase_analyzer = historical_phase_analyzer
        self.global_trend_analyzer = global_trend_analyzer
        self.last_signal = None  # Храним последний сигнал

    def set_last_signal(self, signal):
        """Сохраняет последний сигнал"""
        self.last_signal = signal

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        message = """
🤖 SmartMoneyAI v3

Доступные команды:
/status - текущий статус системы
/signal - получить текущий анализ и сигнал
/analysis - полный анализ рынка
/help - помощь
        """
        await update.message.reply_text(message.strip())

    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /status"""
        message = """
✅ Система работает
📊 Анализ рынка активен
🔄 Обновление каждые 3 минуты

Используйте /signal для получения текущего анализа
        """
        await update.message.reply_text(message.strip())

    async def handle_signal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /signal - выполняет анализ и отправляет результат"""
        await update.message.reply_text("⏳ Выполняю анализ рынка...")
        
        try:
            # Получаем данные
            market_data = await self.data_feed.get_latest_data()
            
            if market_data["ohlcv"].empty:
                await update.message.reply_text("❌ Ошибка: Нет данных OHLCV")
                return
            
            # Выполняем анализ
            structure_data = self.market_structure_engine.analyze(market_data["ohlcv"])
            liquidity_data = self.liquidity_engine.analyze(market_data["ohlcv"], structure_data)
            
            # SVD анализ
            if market_data.get("trades") and market_data.get("orderbook"):
                svd_data = self.svd_engine.analyze(market_data["trades"], market_data["orderbook"])
            else:
                svd_data = {"intent": "unclear", "confidence": 0}
            
            # TA анализ
            ta_data = self.ta_engine.analyze(market_data["ohlcv"])
            
            # Decision (передаем текущую цену)
            current_price = market_data["ohlcv"]["close"].iloc[-1]
            signal = self.decision_engine.analyze(
                liquidity_data,
                svd_data,
                structure_data,
                ta_data,
                current_price=current_price
            )
            
            # Сохраняем последний сигнал
            self.set_last_signal(signal)
            
            # Форматируем ответ с детальными объяснениями на русском
            from modules.ai_explanations.russian_explainer import RussianExplainer
            
            current_price = market_data["ohlcv"]["close"].iloc[-1]
            signal_type = signal.get('signal', 'WAIT')
            confidence = signal.get('confidence', 0)
            
            # Генерируем детальное объяснение
            detailed_explanation = RussianExplainer.generate_detailed_explanation(
                signal, structure_data, liquidity_data, svd_data, ta_data, current_price
            )
            
            # Проверяем на противоречия
            svd_intent = svd_data.get('intent', 'unclear')
            warning = ""
            if signal_type == "BUY" and svd_intent == "distributing":
                warning = "\n\n⚠️ ВНИМАНИЕ: Противоречие - SVD показывает распределение, но сигнал BUY"
            elif signal_type == "SELL" and svd_intent == "accumulating":
                warning = "\n\n⚠️ ВНИМАНИЕ: Противоречие - SVD показывает накопление, но сигнал SELL"
            
            # НОВОЕ: Торговый сигнал (вход в коридоре)
            trading_entry = signal.get("trading_entry", {})
            trading_section = ""
            if trading_entry.get("entry_signal") != "WAIT":
                entry_signal_type = trading_entry.get("entry_signal", "WAIT")
                entry_price = trading_entry.get("entry_price", current_price)
                entry_confidence = trading_entry.get("entry_confidence", 0.0)
                stop_loss = trading_entry.get("stop_loss", 0)
                take_profit = trading_entry.get("take_profit", 0)
                risk_reward = trading_entry.get("risk_reward_ratio", 0.0)
                entry_reason = trading_entry.get("entry_reason", "")
                
                trading_section = f"""

📊 ТОРГОВЫЙ СИГНАЛ (коридор + накопление):
🎯 {entry_signal_type} от ${entry_price:.2f}
📈 Уверенность: {entry_confidence:.1f}/1.0
🛑 Стоп-лосс: ${stop_loss:.2f}
🎯 Тейк-профит: ${take_profit:.2f}
📊 R/R: {risk_reward:.2f}
💡 {entry_reason}
"""
            
            # Формируем сообщение
            message = f"""
📊 ТЕКУЩИЙ АНАЛИЗ РЫНКА

💰 Цена: ${current_price:,.2f}

🎯 СИГНАЛ: {signal_type}
📈 Уверенность: {confidence:.1f}/10
{warning}
{trading_section}
{detailed_explanation}

💡 Используйте /analysis для полного глубокого анализа с прогнозами
            """
            
            await update.message.reply_text(message.strip())
            
        except Exception as e:
            logger.error(f"Ошибка в handle_signal: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Ошибка при анализе: {str(e)}")

    async def handle_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /analysis - полный детальный анализ"""
        await update.message.reply_text("⏳ Выполняю глубокий анализ рынка...")
        
        try:
            from modules.ai_explanations.deep_analyzer import DeepMarketAnalyzer
            
            market_data = await self.data_feed.get_latest_data()
            
            if market_data["ohlcv"].empty:
                await update.message.reply_text("❌ Ошибка: Нет данных")
                return
            
            structure_data = self.market_structure_engine.analyze(market_data["ohlcv"])
            liquidity_data = self.liquidity_engine.analyze(market_data["ohlcv"], structure_data)
            
            # Получаем HTF данные для исторического анализа
            from config import Config
            config = Config()
            htf1_df = await self.data_feed.get_ohlcv_tf(config.HTF_1_INTERVAL)
            htf2_df = await self.data_feed.get_ohlcv_tf(config.HTF_2_INTERVAL)
            htf1_struct = self.market_structure_engine.analyze(htf1_df) if not htf1_df.empty else {"trend": "unknown"}
            htf2_struct = self.market_structure_engine.analyze(htf2_df) if not htf2_df.empty else {"trend": "unknown"}
            
            # Исторический анализ фаз на HTF
            htf1_phases = {}
            htf2_phases = {}
            global_trend = {}
            if self.historical_phase_analyzer and self.global_trend_analyzer:
                if not htf1_df.empty:
                    htf1_phases = self.historical_phase_analyzer.analyze_historical_phases(htf1_df, timeframe_name="HTF1 (1h)")
                if not htf2_df.empty:
                    htf2_phases = self.historical_phase_analyzer.analyze_historical_phases(htf2_df, timeframe_name="HTF2 (4h)")
                global_trend = self.global_trend_analyzer.analyze_global_trend(
                    htf1_struct, htf2_struct, htf1_phases, htf2_phases
                )
            
            if market_data.get("trades") and market_data.get("orderbook"):
                svd_data = self.svd_engine.analyze(market_data["trades"], market_data["orderbook"])
            else:
                svd_data = {"intent": "unclear", "confidence": 0}
            
            ta_data = self.ta_engine.analyze(market_data["ohlcv"])
            signal = self.decision_engine.analyze(liquidity_data, svd_data, structure_data, ta_data)
            
            current_price = market_data["ohlcv"]["close"].iloc[-1]
            
            # Глубокий анализ (передаём исторические фазы и глобальный тренд)
            deep_analyzer = DeepMarketAnalyzer()
            deep_report = deep_analyzer.generate_full_report(
                liquidity_data, structure_data, svd_data, ta_data, current_price, 
                decision_result=signal,
                htf1_phases=htf1_phases,
                htf2_phases=htf2_phases,
                global_trend=global_trend
            )
            
            # Формируем глубокий отчет
            message_parts = []
            
            # Заголовок
            message_parts.append(f"📊 ГЛУБОКИЙ АНАЛИЗ РЫНКА")
            message_parts.append(f"💰 Текущая цена: ${current_price:,.2f}")
            message_parts.append(f"🎯 Сигнал: {signal.get('signal', 'WAIT')} (Confidence: {signal.get('confidence', 0):.1f}/10)")
            message_parts.append("")
            
            # Зоны ликвидности
            message_parts.append("💧 ЗОНЫ ЛИКВИДНОСТИ:")
            liq_analysis = deep_report["liquidity_analysis"]
            
            if liq_analysis["above_price"]:
                above_count = len(liq_analysis["above_price"])
                nearest_above = liq_analysis["nearest_targets"].get("above", {})
                if nearest_above:
                    message_parts.append(f"🟥 НАД ЦЕНОЙ: {above_count} зон")
                    message_parts.append(f"   Ближайшая: ${nearest_above['price']:.2f} (+{nearest_above['distance_pct']:.2f}%)")
                    message_parts.append(f"   Тип: {nearest_above['type']} ({nearest_above['source']})")
            
            if liq_analysis["below_price"]:
                below_count = len(liq_analysis["below_price"])
                nearest_below = liq_analysis["nearest_targets"].get("below", {})
                if nearest_below:
                    message_parts.append(f"🟦 ПОД ЦЕНОЙ: {below_count} зон")
                    message_parts.append(f"   Ближайшая: ${nearest_below['price']:.2f} (-{nearest_below['distance_pct']:.2f}%)")
                    message_parts.append(f"   Тип: {nearest_below['type']} ({nearest_below['source']})")
            
            # Отработанные (swept) уровни - теперь зоны интереса китов
            swept_levels = liq_analysis.get("swept_levels", [])
            if swept_levels:
                message_parts.append("")
                message_parts.append("🎯 ОТРАБОТАННЫЕ УРОВНИ (зоны интереса китов):")
                for swept in swept_levels[:5]:  # Показываем топ-5
                    price = swept.get("price", 0)
                    role = swept.get("role", "")
                    count = swept.get("count", 1)
                    distance = swept.get("distance_pct", 0)
                    candles_ago = swept.get("candles_ago")
                    
                    role_emoji = "🛡️" if role == "support" else "🚧"
                    direction_text = "sweep вниз" if swept.get("direction") == "down" else "sweep вверх"
                    
                    # Время swept
                    time_info = ""
                    if candles_ago:
                        if candles_ago < 10:
                            time_info = f", {candles_ago} свечей назад (недавно)"
                        elif candles_ago < 50:
                            time_info = f", {candles_ago} свечей назад"
                        else:
                            time_info = f", {candles_ago} свечей назад (исторический)"
                    
                    message_parts.append(f"{role_emoji} ${price:.2f} ({distance:.2f}%) - {role}")
                    message_parts.append(f"   {direction_text}, swept {count}x{time_info} - стопы собраны")
            
            message_parts.append("")
            
            # Прогноз движения цены
            message_parts.append("📈 ПРОГНОЗ ДВИЖЕНИЯ ЦЕНЫ:")
            forecast = deep_report["forecast"]
            
            if forecast.get("short_term"):
                st = forecast["short_term"]
                message_parts.append(f"⏱️ КРАТКОСРОЧНО ({st.get('timeframe', '1-4ч')}):")
                message_parts.append(f"   Направление: {st.get('direction', 'N/A')}")
                message_parts.append(f"   Цель: ${st.get('target', 0):.2f} ({st.get('distance_pct', 0):.2f}%)")
                message_parts.append(f"   Вероятность: {st.get('probability', 'medium')}")
                message_parts.append(f"   Причина: {st.get('reason', '')}")
            
            if forecast.get("long_term"):
                lt = forecast["long_term"]
                message_parts.append(f"🌍 ГЛОБАЛЬНО ({lt.get('timeframe', '1-7д')}):")
                message_parts.append(f"   Направление: {lt.get('direction', 'N/A')}")
                message_parts.append(f"   Цель: ${lt.get('target', 0):.2f} ({lt.get('distance_pct', 0):.2f}%)")
                message_parts.append(f"   Вероятность: {lt.get('probability', 'medium')}")
                message_parts.append(f"   Причина: {lt.get('reason', '')}")
            
            message_parts.append("")
            
            # НОВОЕ: Исторические фазы и глобальный тренд
            historical_phases = deep_report.get("historical_phases", {})
            if historical_phases:
                message_parts.append("🌍 ГЛОБАЛЬНЫЙ ТРЕНД И ИСТОРИЧЕСКИЕ ФАЗЫ:")
                message_parts.append("")
                
                # Глобальный тренд
                global_data = historical_phases.get("global", {})
                if global_data:
                    direction = global_data.get("direction", "neutral")
                    strength = global_data.get("strength", 0.0)
                    consensus = global_data.get("consensus", "neutral")
                    recommendation = global_data.get("recommendation", "")
                    
                    direction_emoji = "📈" if direction == "up" else "📉" if direction == "down" else "⚪"
                    consensus_emoji = "🔥" if consensus in ("strong_up", "strong_down") else "✅" if consensus in ("up", "down") else "⚠️"
                    
                    message_parts.append(f"{direction_emoji} ГЛОБАЛЬНОЕ НАПРАВЛЕНИЕ: {direction.upper()} (сила: {strength:.0%})")
                    message_parts.append(f"{consensus_emoji} Консенсус таймфреймов: {consensus}")
                    message_parts.append(f"   {recommendation}")
                    message_parts.append("")
                
                # HTF1 (1h) фазы
                htf1_data = historical_phases.get("htf1", {})
                if htf1_data:
                    global_trend_1h = htf1_data.get("global_trend", "neutral")
                    current_phase_1h = htf1_data.get("current_phase", "neutral")
                    duration_1h = htf1_data.get("current_duration_hours", 0.0)
                    phase_count_1h = htf1_data.get("phase_count", 0)
                    
                    trend_emoji = "📈" if global_trend_1h == "accumulation" else "📉" if global_trend_1h == "distribution" else "⚪"
                    message_parts.append(f"📊 HTF1 (1ч):")
                    message_parts.append(f"   {trend_emoji} Глобальный тренд: {global_trend_1h}")
                    message_parts.append(f"   Текущая фаза: {current_phase_1h} (длительность: {duration_1h:.1f}ч)")
                    message_parts.append(f"   Всего фаз в истории: {phase_count_1h}")
                    message_parts.append("")
                
                # HTF2 (4h) фазы
                htf2_data = historical_phases.get("htf2", {})
                if htf2_data:
                    global_trend_4h = htf2_data.get("global_trend", "neutral")
                    current_phase_4h = htf2_data.get("current_phase", "neutral")
                    duration_4h = htf2_data.get("current_duration_hours", 0.0)
                    phase_count_4h = htf2_data.get("phase_count", 0)
                    
                    trend_emoji = "📈" if global_trend_4h == "accumulation" else "📉" if global_trend_4h == "distribution" else "⚪"
                    message_parts.append(f"📊 HTF2 (4ч):")
                    message_parts.append(f"   {trend_emoji} Глобальный тренд: {global_trend_4h}")
                    message_parts.append(f"   Текущая фаза: {current_phase_4h} (длительность: {duration_4h:.1f}ч)")
                    message_parts.append(f"   Всего фаз в истории: {phase_count_4h}")
                    message_parts.append("")
            
            # Действия умных денег
            message_parts.append("🧠 ДЕЙСТВИЯ УМНЫХ ДЕНЕГ:")
            smart_money_text = deep_report["smart_money"]
            if smart_money_text:
                smart_money_lines = smart_money_text.split('\n')
                for line in smart_money_lines[:18]:  # немного больше подробностей
                    if line.strip():
                        message_parts.append(line)
            
            message_parts.append("")
            
            # Сценарии развития
            message_parts.append("🎬 СЦЕНАРИИ РАЗВИТИЯ СОБЫТИЙ:")
            scenarios = deep_report["scenarios"]
            for i, scenario in enumerate(scenarios[:3], 1):  # Показываем до 3 сценариев
                message_parts.append(f"\n{i}. {scenario.get('name', 'Сценарий')} ({scenario.get('probability', 'medium')} вероятность):")
                message_parts.append(f"   {scenario.get('description', '')}")
                message_parts.append(f"   Цель: ${scenario.get('target', 'N/A')}")
                message_parts.append(f"   Срок: {scenario.get('timeframe', 'N/A')}")
            
            message_parts.append("")
            
            # НОВОЕ: Торговый сигнал (вход в коридоре при накоплении)
            trading_entry = signal.get("trading_entry", {})
            if trading_entry.get("entry_signal") != "WAIT":
                message_parts.append("📊 ТОРГОВЫЙ СИГНАЛ (коридор + накопление):")
                entry_signal_type = trading_entry.get("entry_signal", "WAIT")
                entry_price = trading_entry.get("entry_price", current_price)
                entry_confidence = trading_entry.get("entry_confidence", 0.0)
                stop_loss = trading_entry.get("stop_loss", 0)
                take_profit = trading_entry.get("take_profit", 0)
                risk_reward = trading_entry.get("risk_reward_ratio", 0.0)
                entry_reason = trading_entry.get("entry_reason", "")
                
                signal_emoji = "🟢" if entry_signal_type == "BUY" else "🔴" if entry_signal_type == "SELL" else "🟡"
                message_parts.append(f"{signal_emoji} {entry_signal_type} от ${entry_price:.2f}")
                message_parts.append(f"📈 Уверенность входа: {entry_confidence:.1f}/1.0")
                message_parts.append(f"🛑 Стоп-лосс: ${stop_loss:.2f}")
                message_parts.append(f"🎯 Тейк-профит: ${take_profit:.2f}")
                message_parts.append(f"📊 Risk/Reward: {risk_reward:.2f}")
                message_parts.append(f"💡 {entry_reason}")
                
                # Информация о коридоре
                range_data = signal.get("range_data", {})
                if range_data.get("is_range"):
                    range_low = range_data.get("range_low", 0)
                    range_high = range_data.get("range_high", 0)
                    range_width = range_data.get("range_width_pct", 0.0)
                    current_position = range_data.get("current_position", "middle")
                    message_parts.append("")
                    message_parts.append(f"📊 Коридор: ${range_low:.2f} - ${range_high:.2f} (ширина: {range_width:.2f}%)")
                    message_parts.append(f"📍 Позиция цены в коридоре: {current_position}")
                message_parts.append("")
            
            # Практические рекомендации
            recommendations = deep_report.get("recommendations", [])
            if recommendations:
                message_parts.append("💡 ЧТО ДЕЛАТЬ СЕЙЧАС:")
                message_parts.append("")
                for rec in recommendations:
                    variant = rec.get("variant", "")
                    title = rec.get("title", "")
                    points = rec.get("points", [])
                    
                    message_parts.append(f"Вариант {variant}: {title}")
                    for point in points:
                        message_parts.append(f"   • {point}")
                    message_parts.append("")
            
            message_parts.append("📊 ДЕТАЛИ:")
            message_parts.append(f"• Структура: {structure_data.get('trend', 'unknown')}")
            message_parts.append(f"• Ликвидность: {liquidity_data.get('direction', {}).get('direction', 'neutral')}")
            message_parts.append(f"• SVD Intent: {svd_data.get('intent', 'unclear')}")
            message_parts.append(f"• Delta (краткосрочно): {svd_data.get('delta', 0):.2f}")
            message_parts.append(f"• CVD (накопительная): {svd_data.get('cvd', 0):.2f}")
            message_parts.append(f"• CVD slope: {svd_data.get('cvd_slope', 0):.2f}")
            message_parts.append(f"• RSI: {ta_data.get('rsi', 0):.1f}")
            
            # Отправляем сообщение (разбиваем если слишком длинное)
            full_message = "\n".join(message_parts)
            if len(full_message) > 4000:  # Telegram лимит ~4096 символов
                # Отправляем частями
                chunk_size = 3500
                chunks = [full_message[i:i+chunk_size] for i in range(0, len(full_message), chunk_size)]
                for chunk in chunks:
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(full_message)
            
        except Exception as e:
            logger.error(f"Ошибка в handle_analysis: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")

    async def handle_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /health - статус системы"""
        if not self.health_monitor:
            await update.message.reply_text("❌ Мониторинг недоступен")
            return
        
        status = self.health_monitor.get_status()
        
        status_icon = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌"
        }
        icon = status_icon.get(status["status"], "❓")
        
        message = f"""
{icon} СТАТУС СИСТЕМЫ: {status['status'].upper()}

⏱ Время работы: {status['uptime_hours']:.1f}ч

📊 СИГНАЛЫ:
   Всего: {status['signal_count']}
   BUY: {status['signal_types']['BUY']}
   SELL: {status['signal_types']['SELL']}
   WAIT: {status['signal_types']['WAIT']}
   Последний: {status['last_signal_seconds_ago']:.0f}с назад

📡 API/WS:
   API вызовы: {status['api_calls']}
   API ошибки: {status['api_errors']}
   Success rate: {status['api_success_rate']:.1%}
   WS reconnects: {status['ws_reconnects']}

💻 СИСТЕМА:
   CPU: {status['system']['cpu_percent']:.1f}%
   Память: {status['system']['memory_percent']:.1f}%
   Доступно: {status['system']['memory_available_mb']:.0f}MB

❌ Ошибки: {status['error_count']}
        """
        await update.message.reply_text(message.strip())

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        message = """
📖 Помощь по SmartMoneyAI v3

Система автоматически анализирует рынок и отправляет сигналы.

Команды:
/start - начать работу
/status - статус системы
/signal - получить текущий анализ и сигнал
/analysis - полный детальный анализ рынка
/health - состояние системы и метрики
/help - эта справка

💡 Используйте /signal для получения актуального анализа по требованию

🚨 Алерты:
Бот автоматически отправляет уведомления о важных событиях:
• Смена фазы (execution, distribution)
• Разворот CVD (accumulating ↔ distributing)
• Сильные сигналы (confidence >= 7.0)
        """
        await update.message.reply_text(message.strip())
    
    async def send_alert(self, alert_message):
        """
        Отправка алерта всем подписанным пользователям
        
        Args:
            alert_message: текст алерта
        """
        try:
            # Пока логируем алерты
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"🚨 АЛЕРТ: {alert_message}")
            
            # TODO: Реализовать отправку в Telegram всем активным пользователям
            # Нужно хранить список chat_id активных пользователей в базе
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка отправки алерта: {e}")

