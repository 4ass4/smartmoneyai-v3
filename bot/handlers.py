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
                 svd_engine, market_structure_engine, ta_engine):
        self.bot = bot
        self.decision_engine = decision_engine
        self.data_feed = data_feed
        self.liquidity_engine = liquidity_engine
        self.svd_engine = svd_engine
        self.market_structure_engine = market_structure_engine
        self.ta_engine = ta_engine
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
            
            # Формируем сообщение
            message = f"""
📊 ТЕКУЩИЙ АНАЛИЗ РЫНКА

💰 Цена: ${current_price:,.2f}

🎯 СИГНАЛ: {signal_type}
📈 Уверенность: {confidence:.1f}/10
{warning}

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
            
            if market_data.get("trades") and market_data.get("orderbook"):
                svd_data = self.svd_engine.analyze(market_data["trades"], market_data["orderbook"])
            else:
                svd_data = {"intent": "unclear", "confidence": 0}
            
            ta_data = self.ta_engine.analyze(market_data["ohlcv"])
            signal = self.decision_engine.analyze(liquidity_data, svd_data, structure_data, ta_data)
            
            current_price = market_data["ohlcv"]["close"].iloc[-1]
            
            # Глубокий анализ
            deep_analyzer = DeepMarketAnalyzer()
            deep_report = deep_analyzer.generate_full_report(
                liquidity_data, structure_data, svd_data, ta_data, current_price
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
            
            # Действия умных денег
            message_parts.append("🧠 ДЕЙСТВИЯ УМНЫХ ДЕНЕГ:")
            smart_money_text = deep_report["smart_money"]
            if smart_money_text:
                # Разбиваем на части если слишком длинное
                smart_money_lines = smart_money_text.split('\n')
                for line in smart_money_lines[:10]:  # Ограничиваем длину
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
            message_parts.append("📊 ДЕТАЛИ:")
            message_parts.append(f"• Структура: {structure_data.get('trend', 'unknown')}")
            message_parts.append(f"• Ликвидность: {liquidity_data.get('direction', {}).get('direction', 'neutral')}")
            message_parts.append(f"• SVD Intent: {svd_data.get('intent', 'unclear')}")
            message_parts.append(f"• Delta: {svd_data.get('delta', 0):.2f}")
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
/help - эта справка

💡 Используйте /signal для получения актуального анализа по требованию
        """
        await update.message.reply_text(message.strip())

