# modules/ai_explanations/russian_explainer.py

"""
Русскоязычные объяснения с конкретизацией
"""


class RussianExplainer:
    """Генератор понятных объяснений на русском"""

    @staticmethod
    def explain_structure(trend):
        """Объяснение структуры рынка"""
        explanations = {
            "bullish": "📈 Бычий тренд - рынок растет, формируются Higher Highs и Higher Lows",
            "bearish": "📉 Медвежий тренд - рынок падает, формируются Lower Highs и Lower Lows",
            "range": "↔️ Боковой диапазон - рынок движется в коридоре, нет четкого направления",
            "unknown": "❓ Структура неопределенная - недостаточно данных"
        }
        return explanations.get(trend, f"Структура: {trend}")

    @staticmethod
    def explain_liquidity_direction(direction):
        """Объяснение направления ликвидности"""
        explanations = {
            "up": "🟥 Ликвидность НАД ценой - больше стопов покупателей, цена может пойти вверх чтобы их собрать",
            "down": "🟦 Ликвидность ПОД ценой - больше стопов продавцов, цена может пойти вниз чтобы их собрать",
            "neutral": "⚪ Ликвидность сбалансирована - нет явного преимущества вверх или вниз"
        }
        return explanations.get(direction, f"Направление: {direction}")

    @staticmethod
    def explain_svd_intent(intent, delta, cvd=None, cvd_slope=None, is_pullback=False):
        """Объяснение намерений умных денег с CVD"""
        delta_abs = abs(delta)
        
        if intent == "accumulating":
            if delta_abs > 50:
                msg = f"💰 СИЛЬНОЕ НАКОПЛЕНИЕ - крупные игроки активно покупают"
            else:
                msg = f"💰 Накопление позиций - крупные игроки постепенно покупают"
            msg += f"\n   • Дельта (краткосрочно): {delta:+.2f}"
            if cvd is not None:
                msg += f"\n   • CVD (накопительная): {cvd:+.2f}"
            if cvd_slope is not None:
                slope_desc = 'растёт' if cvd_slope > 0 else 'падает' if cvd_slope < 0 else 'стабильна'
                msg += f"\n   • CVD slope: {cvd_slope:+.2f} — {slope_desc}"
                if is_pullback and cvd_slope < 0:
                    msg += "\n   ⚠️ Краткосрочная пауза/коррекция в накоплении (общий тренд накопление)"
            return msg
        elif intent == "distributing":
            if delta_abs > 50:
                msg = f"📉 СИЛЬНОЕ РАСПРЕДЕЛЕНИЕ - крупные игроки активно продают"
            else:
                msg = f"📉 Распределение позиций - крупные игроки постепенно продают"
            msg += f"\n   • Дельта (краткосрочно): {delta:+.2f}"
            if cvd is not None:
                msg += f"\n   • CVD (накопительная): {cvd:+.2f}"
            if cvd_slope is not None:
                slope_desc = 'падает' if cvd_slope < 0 else 'растёт' if cvd_slope > 0 else 'стабильна'
                msg += f"\n   • CVD slope: {cvd_slope:+.2f} — {slope_desc}"
                if is_pullback and cvd_slope > 0:
                    msg += "\n   ⚠️ Краткосрочный отскок в распределении (общий тренд распределение)"
            return msg
        else:
            msg = f"❓ Намерения неясны"
            msg += f"\n   • Дельта (краткосрочно): {delta:+.2f}"
            if cvd is not None:
                msg += f"\n   • CVD (накопительная): {cvd:+.2f}"
            return msg

    @staticmethod
    def explain_rsi(rsi):
        """Объяснение RSI"""
        if rsi > 70:
            return f"🔴 RSI {rsi:.1f} - ПЕРЕКУПЛЕННОСТЬ (риск коррекции вниз)"
        elif rsi < 30:
            return f"🟢 RSI {rsi:.1f} - ПЕРЕПРОДАННОСТЬ (возможен отскок вверх)"
        elif rsi > 50:
            return f"🟡 RSI {rsi:.1f} - Бычья зона (преобладают покупатели)"
        else:
            return f"🟡 RSI {rsi:.1f} - Медвежья зона (преобладают продавцы)"

    @staticmethod
    def explain_ta_trend(trend, ema_fast, ema_slow, current_price):
        """Объяснение технического тренда"""
        if trend == "bullish":
            ema_status = "выше" if current_price > ema_fast else "ниже"
            return f"📈 Бычий тренд - цена {ema_status} быстрой EMA ({ema_fast:.2f})"
        elif trend == "bearish":
            ema_status = "выше" if current_price > ema_fast else "ниже"
            return f"📉 Медвежий тренд - цена {ema_status} быстрой EMA ({ema_fast:.2f})"
        else:
            return f"⚪ Нейтральный тренд - EMA Fast: {ema_fast:.2f}, EMA Slow: {ema_slow:.2f}"

    @staticmethod
    def explain_confidence(confidence):
        """Объяснение уровня уверенности"""
        if confidence >= 8:
            return "🔥 ОЧЕНЬ ВЫСОКАЯ уверенность - сигнал очень сильный"
        elif confidence >= 6:
            return "✅ ВЫСОКАЯ уверенность - сигнал надежный"
        elif confidence >= 4:
            return "⚠️ СРЕДНЯЯ уверенность - сигнал требует осторожности"
        elif confidence >= 2:
            return "⚠️ НИЗКАЯ уверенность - сигнал слабый, много неопределенности"
        else:
            return "❌ ОЧЕНЬ НИЗКАЯ уверенность - сигнал ненадежный"

    @staticmethod
    def generate_detailed_explanation(signal_data, structure_data, liquidity_data, svd_data, ta_data, current_price):
        """Генерация детального объяснения"""
        signal = signal_data.get('signal', 'WAIT')
        confidence = signal_data.get('confidence', 0)
        
        parts = []
        
        # Основной сигнал
        if signal == "BUY":
            parts.append("🟢 СИГНАЛ НА ПОКУПКУ")
        elif signal == "SELL":
            parts.append("🔴 СИГНАЛ НА ПРОДАЖУ")
        else:
            parts.append("🟡 ОЖИДАНИЕ")
        
        # Уверенность
        parts.append(f"\n📊 {RussianExplainer.explain_confidence(confidence)}")
        
        # Структура
        trend = structure_data.get('trend', 'unknown')
        parts.append(f"\n📈 СТРУКТУРА РЫНКА:")
        parts.append(f"   {RussianExplainer.explain_structure(trend)}")
        
        # Ликвидность
        liq_dir = liquidity_data.get('direction', {}).get('direction', 'neutral')
        parts.append(f"\n💧 ЛИКВИДНОСТЬ:")
        parts.append(f"   {RussianExplainer.explain_liquidity_direction(liq_dir)}")
        
        # SVD
        svd_intent = svd_data.get('intent', 'unclear')
        delta = svd_data.get('delta', 0)
        cvd = svd_data.get('cvd', None)
        cvd_slope = svd_data.get('cvd_slope', None)
        is_pullback = svd_data.get('is_pullback_or_bounce', False)
        parts.append(f"\n🧠 УМНЫЕ ДЕНЬГИ:")
        parts.append(f"   {RussianExplainer.explain_svd_intent(svd_intent, delta, cvd, cvd_slope, is_pullback)}")
        # Доп. признаки манипуляций/потока
        dom = svd_data.get("dom_imbalance", {})
        thin = svd_data.get("thin_zones", {})
        spoof = svd_data.get("spoof_wall", {})
        spoof_confirmed = svd_data.get("spoof_confirmed", False)
        spoof_duration = svd_data.get("spoof_duration_ms", 0)
        sweeps = liquidity_data.get("sweeps", {})
        fomo = svd_data.get("fomo", False)
        panic = svd_data.get("panic", False)
        strong_fomo = svd_data.get("strong_fomo", False)
        strong_panic = svd_data.get("strong_panic", False)
        phase = svd_data.get("phase", "discovery")
        htf_liq = signal_data.get("htf_liq", {})
        liq1 = htf_liq.get("htf1", {}).get("direction", "neutral") if isinstance(htf_liq, dict) else "neutral"
        liq2 = htf_liq.get("htf2", {}).get("direction", "neutral") if isinstance(htf_liq, dict) else "neutral"

        # Расшифровки манипуляций/фаз
        manip_parts = []
        if dom.get("side") == "bid":
            manip_parts.append("DOM: дисбаланс в покупках")
        if dom.get("side") == "ask":
            manip_parts.append("DOM: дисбаланс в продажах")
        if thin.get("thin_above"):
            manip_parts.append("Сверху тонкая ликвидность — возможен быстрый шип вверх")
        if thin.get("thin_below"):
            manip_parts.append("Снизу тонкая ликвидность — возможен быстрый шип вниз")
        if spoof.get("side") or spoof_confirmed:
            side = spoof.get("side", "")
            txt = "Спуф-стенка" + (f" ({side})" if side else "")
            if spoof_duration:
                txt += f", жила {spoof_duration/1000:.1f}с"
            if spoof_confirmed:
                txt += " — подтверждена"
            manip_parts.append(txt)
        if sweeps.get("sweep_up"):
            manip_parts.append("Свип вверх (прокол хай с возвратом)")
        if sweeps.get("sweep_down"):
            manip_parts.append("Свип вниз (прокол лоу с возвратом)")
        if sweeps.get("post_reversal"):
            manip_parts.append("После свипа — реверс внутрь диапазона")
        if fomo:
            manip_parts.append("FOMO: ускоренный приток покупок")
        if panic:
            manip_parts.append("Panic: ускоренный приток продаж")
        if strong_fomo:
            manip_parts.append("Сильное FOMO (серия покупок + волатильность)")
        if strong_panic:
            manip_parts.append("Сильная паника (серия продаж + волатильность)")
        manip_parts.append(f"Фаза: {phase}")
        manip_parts.append(f"HTF ликвидность: 1) {liq1}, 2) {liq2}")
        # Эвристика многократных отказов и "последний свип"
        if liq_dir == "up" and dom.get("side") == "ask" and phase in ("distribution", "manipulation"):
            manip_parts.append("Многократные тесты верхней ликвидности без закрепления — давление sell walls, риск протяжки вниз")
            manip_parts.append("Возможен последний свип вверх для снятия стопов перед сливом")
        if liq_dir == "down" and dom.get("side") == "bid" and phase in ("accumulation", "manipulation"):
            manip_parts.append("Многократные тесты нижней ликвидности без пробоя — bids держат, набор позиций")
            manip_parts.append("Возможен последний свип вниз для снятия стопов перед разворотом вверх")
        if manip_parts:
            parts.append("\n🎭 МАНИПУЛЯЦИИ/ФАКТОРЫ ПОТОКА:")
            for m in manip_parts:
                parts.append(f"   • {m}")
            # Краткие пояснения по терминам, чтобы не оставлять сухие факты
            explanations = []
            if dom.get("side"):
                explanations.append("DOM: дисбаланс лимитных ордеров — куда перевешивают стенки (bid = поддержка, ask = давление).")
            if thin.get("thin_above") or thin.get("thin_below"):
                explanations.append("Тонкая ликвидность: мало лимиток — цена может резко проскочить в эту сторону.")
            if spoof.get("side") or spoof_confirmed:
                explanations.append("Спуф-стенка: крупный лимитный ордер, который может быть фейком для манипуляции потоком.")
            explanations.append("Фаза: market-flow стадия по SVD (manipulation/distribution/execution/discovery).")
            explanations.append("HTF ликвидность: смещение ликвидности на старших ТФ (1ч/4ч), если есть перекос.")
            parts.append("   Пояснения:")
            for e in explanations:
                parts.append(f"   - {e}")
        
        # TA
        ta_trend = ta_data.get('trend', 'neutral')
        ema_fast = ta_data.get('ema_fast', 0)
        ema_slow = ta_data.get('ema_slow', 0)
        rsi = ta_data.get('rsi', 0)
        parts.append(f"\n📉 ТЕХНИЧЕСКИЙ АНАЛИЗ:")
        parts.append(f"   {RussianExplainer.explain_ta_trend(ta_trend, ema_fast, ema_slow, current_price)}")
        parts.append(f"   {RussianExplainer.explain_rsi(rsi)}")
        
        return "\n".join(parts)

