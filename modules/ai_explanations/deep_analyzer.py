# modules/ai_explanations/deep_analyzer.py

"""
Глубокий анализ рынка с объяснением действий умных денег
"""


class DeepMarketAnalyzer:
    """
    Глубокий анализ с объяснением:
    - Где находится ликвидность
    - Куда пойдет цена (глобально и краткосрочно)
    - Действия умных денег
    - Сценарии развития событий
    """

    def __init__(self):
        pass

    def analyze_liquidity_zones(self, liquidity_data, structure_data, current_price):
        """
        Анализ зон ликвидности с конкретными уровнями
        """
        analysis = {
            "above_price": [],
            "below_price": [],
            "nearest_targets": {},
            "swept_levels": []  # Отработанные уровни (теперь зоны интереса)
        }

        # Анализ стоп-кластеров
        stop_clusters = liquidity_data.get("stop_clusters", [])
        for cluster in stop_clusters:
            price = cluster.get("price", 0)
            cluster_type = cluster.get("type", "")
            if price > current_price and cluster_type == "buy_stops":
                analysis["above_price"].append({
                    "price": price,
                    "type": "buy_stops",
                    "source": cluster.get("source", "unknown"),
                    "distance_pct": ((price - current_price) / current_price) * 100
                })
            elif price < current_price and cluster_type == "sell_stops":
                analysis["below_price"].append({
                    "price": price,
                    "type": "sell_stops",
                    "source": cluster.get("source", "unknown"),
                    "distance_pct": ((current_price - price) / current_price) * 100
                })

        # Анализ swing liquidity
        swing_liq = liquidity_data.get("swing_liquidity", [])
        for swing in swing_liq:
            price = swing.get("price", 0)
            swing_type = swing.get("type", "")
            if price > current_price and swing_type == "buy_stops":
                analysis["above_price"].append({
                    "price": price,
                    "type": "buy_stops",
                    "source": "swing_high",
                    "distance_pct": ((price - current_price) / current_price) * 100
                })
            elif price < current_price and swing_type == "sell_stops":
                analysis["below_price"].append({
                    "price": price,
                    "type": "sell_stops",
                    "source": "swing_low",
                    "distance_pct": ((current_price - price) / current_price) * 100
                })

        # Сортируем по расстоянию
        analysis["above_price"].sort(key=lambda x: x["distance_pct"])
        analysis["below_price"].sort(key=lambda x: x["distance_pct"], reverse=True)

        # Ближайшие цели
        if analysis["above_price"]:
            analysis["nearest_targets"]["above"] = analysis["above_price"][0]
        if analysis["below_price"]:
            analysis["nearest_targets"]["below"] = analysis["below_price"][0]
        
        # Отработанные (swept) уровни - теперь это зоны интереса/support/resistance
        swept_levels = liquidity_data.get("swept_levels", [])
        for swept in swept_levels:
            price = swept.get("price", 0)
            direction = swept.get("direction", "")
            count = swept.get("count", 1)
            candles_ago = swept.get("candles_ago")
            reason = swept.get("reason", "")
            
            # Определяем как работает swept уровень теперь
            if price < current_price:
                # Swept вниз → теперь это support
                role = "support"
            else:
                # Swept вверх → теперь это resistance
                role = "resistance"
            
            swept_info = {
                "price": price,
                "direction": direction,
                "count": count,
                "role": role,
                "distance_pct": abs((price - current_price) / current_price) * 100
            }
            
            if candles_ago:
                swept_info["candles_ago"] = candles_ago
            if reason:
                swept_info["reason"] = reason
            
            analysis["swept_levels"].append(swept_info)

        return analysis

    def generate_price_movement_forecast(self, liquidity_data, structure_data, svd_data, current_price, liquidity_analysis):
        """
        Генерация прогноза движения цены к ликвидности
        УЧИТЫВАЕТ: действия китов (SVD intent), фазу manipulation, ловушки
        """
        forecast = {
            "short_term": {},
            "long_term": {},
            "scenarios": []
        }

        liq_direction = liquidity_data.get("direction", {}).get("direction", "neutral")
        svd_intent = svd_data.get("intent", "unclear")
        phase = svd_data.get("phase", "discovery")
        trend = structure_data.get("trend", "range")
        cvd_value = svd_data.get("cvd", 0)
        cvd_reversal = svd_data.get("cvd_reversal_detected", False)
        
        nearest_above = liquidity_analysis.get("nearest_targets", {}).get("above")
        nearest_below = liquidity_analysis.get("nearest_targets", {}).get("below")
        
        # Проверяем был ли недавний sweep (trap уже завершён?)
        sweeps = liquidity_data.get("sweeps", {})
        recent_sweep_down = sweeps.get("sweep_down", False) and sweeps.get("post_reversal", False)
        recent_sweep_up = sweeps.get("sweep_up", False) and sweeps.get("post_reversal", False)
        
        # === ЛОГИКА SMART MONEY ===
        # ВАЖНО: Различаем trap ДО и ПОСЛЕ sweep!
        
        is_trap_scenario = False
        trap_completed = False  # Trap уже завершён?
        
        # СЛУЧАЙ 1: Trap УЖЕ ЗАВЕРШЁН (был sweep + разворот)
        # Если был sweep вниз + accumulating → trap завершён, ожидается РОСТ
        if recent_sweep_down and svd_intent == "accumulating":
            trap_completed = True
            is_trap_scenario = False  # Trap завершён, теперь нормальное движение вверх
        
        # Если был sweep вверх + distributing → trap завершён, ожидается ПАДЕНИЕ
        elif recent_sweep_up and svd_intent == "distributing":
            trap_completed = True
            is_trap_scenario = False  # Trap завершён, теперь нормальное движение вниз
        
        # СЛУЧАЙ 2: Trap ВПЕРЕДИ (не было sweep, но есть противоречие)
        # Если accumulating + liq_down + НЕТ sweep → trap впереди
        elif svd_intent == "accumulating" and liq_direction == "down" and not recent_sweep_down:
            is_trap_scenario = True  # Bear trap впереди: свип вниз → разворот вверх
        
        # Если distributing + liq_up + НЕТ sweep → trap впереди
        elif svd_intent == "distributing" and liq_direction == "up" and not recent_sweep_up:
            is_trap_scenario = True  # Bull trap впереди: свип вверх → разворот вниз
        
        # СЛУЧАЙ 3: РАЗВОРОТ ТРЕНДА обнаружен (CVD reversal)
        # Если обнаружен разворот → ожидается движение в сторону нового тренда
        elif cvd_reversal:
            trap_completed = False
            is_trap_scenario = False  # Разворот, движение в сторону нового intent
        
        # Дополнительная уверенность если фаза manipulation/execution
        trap_probability = "high" if phase == "manipulation" else "medium"
        
        # === КРАТКОСРОЧНЫЙ ПРОГНОЗ (1-4ч) ===
        
        # ПРИОРИТЕТ 1: Trap уже завершён → движение в сторону SVD intent
        if trap_completed:
            if svd_intent == "accumulating" and nearest_above:
                # Sweep вниз завершён, accumulating → РОСТ вверх
                forecast["short_term"] = {
                    "direction": "UP",
                    "target": nearest_above["price"],
                    "distance_pct": nearest_above["distance_pct"],
                    "reason": f"Sweep вниз завершён, киты накапливают → движение к ${nearest_above['price']:.2f}",
                    "probability": "high" if phase == "execution" else "medium",
                    "timeframe": "1-4ч",
                    "is_sweep": False
                }
            elif svd_intent == "distributing" and nearest_below:
                # Sweep вверх завершён, distributing → ПАДЕНИЕ вниз
                forecast["short_term"] = {
                    "direction": "DOWN",
                    "target": nearest_below["price"],
                    "distance_pct": nearest_below["distance_pct"],
                    "reason": f"Sweep вверх завершён, киты распределяют → движение к ${nearest_below['price']:.2f}",
                    "probability": "high" if phase == "execution" else "medium",
                    "timeframe": "1-4ч",
                    "is_sweep": False
                }
        
        # ПРИОРИТЕТ 2: Trap впереди → сначала sweep
        elif is_trap_scenario:
            if svd_intent == "accumulating" and nearest_below:
                # Киты накапливают, но сначала свип вниз
                forecast["short_term"] = {
                    "direction": "DOWN (свип)",
                    "target": nearest_below["price"],
                    "distance_pct": nearest_below["distance_pct"],
                    "reason": f"Свип вниз к ${nearest_below['price']:.2f} (собрать стопы лонгов) перед разворотом вверх",
                    "probability": trap_probability,
                    "timeframe": "1-4ч",
                    "is_sweep": True
                }
            elif svd_intent == "distributing" and nearest_above:
                # Киты распределяют, но сначала свип вверх
                forecast["short_term"] = {
                    "direction": "UP (свип)",
                    "target": nearest_above["price"],
                    "distance_pct": nearest_above["distance_pct"],
                    "reason": f"Свип вверх к ${nearest_above['price']:.2f} (собрать стопы шортов) перед разворотом вниз",
                    "probability": trap_probability,
                    "timeframe": "1-4ч",
                    "is_sweep": True
                }
        
        # ПРИОРИТЕТ 3: Нормальное движение в сторону ликвидности
        else:
            # Движение в сторону SVD intent (приоритет) или liquidity
            if svd_intent == "accumulating" and nearest_above:
                forecast["short_term"] = {
                    "direction": "UP",
                    "target": nearest_above["price"],
                    "distance_pct": nearest_above["distance_pct"],
                    "reason": f"Киты накапливают → движение к ликвидности ${nearest_above['price']:.2f}",
                    "probability": "high" if phase == "execution" else "medium",
                    "timeframe": "1-4ч"
                }
            elif svd_intent == "distributing" and nearest_below:
                forecast["short_term"] = {
                    "direction": "DOWN",
                    "target": nearest_below["price"],
                    "distance_pct": nearest_below["distance_pct"],
                    "reason": f"Киты распределяют → движение к ликвидности ${nearest_below['price']:.2f}",
                    "probability": "high" if phase == "execution" else "medium",
                    "timeframe": "1-4ч"
                }
            # Fallback: liquidity direction
            elif liq_direction == "up" and nearest_above:
                forecast["short_term"] = {
                    "direction": "UP",
                    "target": nearest_above["price"],
                    "distance_pct": nearest_above["distance_pct"],
                    "reason": f"Ликвидность покупателей (buy stops) на уровне ${nearest_above['price']:.2f}",
                    "probability": "medium",
                    "timeframe": "1-4ч"
                }
            elif liq_direction == "down" and nearest_below:
                forecast["short_term"] = {
                    "direction": "DOWN",
                    "target": nearest_below["price"],
                    "distance_pct": nearest_below["distance_pct"],
                    "reason": f"Ликвидность продавцов (sell stops) на уровне ${nearest_below['price']:.2f}",
                    "probability": "medium",
                    "timeframe": "1-4ч"
                }
        
        # === ГЛОБАЛЬНЫЙ ПРОГНОЗ (1-7д) ===
        # ВСЕГДА основан на SVD intent (что делают киты)
        
        # ПРИОРИТЕТ: SVD intent определяет глобальное направление
        if svd_intent == "accumulating" and cvd_value >= 0:
            # Киты накапливают (CVD положительный или растёт) → глобально РОСТ
            if nearest_above:
                forecast["long_term"] = {
                    "direction": "UP",
                    "target": nearest_above["price"],
                    "distance_pct": nearest_above["distance_pct"],
                    "reason": f"Умные деньги накапливают (CVD: {cvd_value:.1f}) - цель ${nearest_above['price']:.2f}",
                    "probability": "high" if (trap_completed or phase == "execution") else "medium",
                    "timeframe": "1-7д"
                }
            else:
                # Fallback на ATH
                ath = liquidity_data.get("ath_atl", {}).get("ath", {}).get("price", 0)
                if ath > current_price:
                    forecast["long_term"] = {
                        "direction": "UP",
                        "target": ath,
                        "distance_pct": ((ath - current_price) / current_price) * 100,
                        "reason": f"Умные деньги накапливают (CVD: {cvd_value:.1f}) - цель ATH ${ath:.2f}",
                        "probability": "medium",
                        "timeframe": "1-7д"
                    }
        
        elif svd_intent == "accumulating" and cvd_value < 0 and cvd_reversal:
            # CVD отрицательный, НО разворот обнаружен → глобально РОСТ (ранний вход)
            if nearest_above:
                forecast["long_term"] = {
                    "direction": "UP",
                    "target": nearest_above["price"],
                    "distance_pct": nearest_above["distance_pct"],
                    "reason": f"Разворот вверх обнаружен (CVD slope растёт) - цель ${nearest_above['price']:.2f}",
                    "probability": "medium",
                    "timeframe": "1-7д"
                }
        
        elif svd_intent == "distributing" and cvd_value <= 0:
            # Киты распределяют (CVD отрицательный или падает) → глобально ПАДЕНИЕ
            if nearest_below:
                forecast["long_term"] = {
                    "direction": "DOWN",
                    "target": nearest_below["price"],
                    "distance_pct": nearest_below["distance_pct"],
                    "reason": f"Умные деньги распределяют (CVD: {cvd_value:.1f}) - цель ${nearest_below['price']:.2f}",
                    "probability": "high" if (trap_completed or phase == "execution") else "medium",
                    "timeframe": "1-7д"
                }
            else:
                # Fallback на ATL
                atl = liquidity_data.get("ath_atl", {}).get("atl", {}).get("price", 0)
                if atl < current_price:
                    forecast["long_term"] = {
                        "direction": "DOWN",
                        "target": atl,
                        "distance_pct": ((current_price - atl) / current_price) * 100,
                        "reason": f"Умные деньги распределяют - цель ATL ${atl:.2f}",
                        "probability": "medium",
                        "timeframe": "1-7д"
                    }
        
        # Fallback для всех случаев: если нет long_term прогноза, используем ATH/ATL based on structure
        if not forecast.get("long_term"):
            ath_atl = liquidity_data.get("ath_atl", {})
            if ath_atl:
                ath = ath_atl.get("ath", {}).get("price", 0)
                atl = ath_atl.get("atl", {}).get("price", 0)
                
                if trend == "bullish" and ath > current_price:
                    forecast["long_term"] = {
                        "direction": "UP",
                        "target": ath,
                        "distance_pct": ((ath - current_price) / current_price) * 100,
                        "reason": f"Бычий тренд - цель ATH ${ath:.2f}",
                        "probability": "medium",
                        "timeframe": "1-7д"
                    }
                elif trend == "bearish" and atl < current_price:
                    forecast["long_term"] = {
                        "direction": "DOWN",
                        "target": atl,
                        "distance_pct": ((current_price - atl) / current_price) * 100,
                        "reason": f"Медвежий тренд - цель ATL ${atl:.2f}",
                        "probability": "medium",
                        "timeframe": "1-7д"
                    }

        return forecast

    def explain_smart_money_actions(self, svd_data, liquidity_data, structure_data):
        """
        Объяснение действий умных денег с акцентом на манипуляции и ловушки
        """
        explanation = []
        
        svd_intent = svd_data.get("intent", "unclear")
        delta = svd_data.get("delta", 0)
        absorption = svd_data.get("absorption", {})
        direction = liquidity_data.get("direction", {}).get("direction", "neutral")
        trend = structure_data.get("trend", "range")

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
        liq_dir = liquidity_data.get("direction", {}).get("direction", "neutral")

        # Намерения (с CVD для полной картины)
        cvd = svd_data.get("cvd", 0)
        cvd_slope = svd_data.get("cvd_slope", 0)
        is_pullback = svd_data.get("is_pullback_or_bounce", False)
        
        if svd_intent == "accumulating":
            explanation.append("💰 УМНЫЕ ДЕНЬГИ НАКАПЛИВАЮТ:")
            explanation.append("• Крупные игроки постепенно покупают и скрывают интерес")
            explanation.append(f"• Дельта (краткосрочно): {delta:+.2f} — текущий перевес покупок")
            explanation.append(f"• CVD (накопительная): {cvd:+.2f} — общий тренд накопления")
            slope_desc = 'растёт' if cvd_slope > 0 else 'падает' if cvd_slope < 0 else 'стабильна'
            explanation.append(f"• CVD slope: {cvd_slope:+.2f} — дельта {slope_desc}")
            if is_pullback and cvd_slope < 0:
                explanation.append("• ⚠️ Краткосрочная пауза/коррекция в накоплении (возможны 2 сценария)")
            if direction == "up":
                explanation.append("• Ликвидность сверху — готовятся тянуть цену к стопам покупателей")
            explanation.append("• Цель: собрать позиции перед потенциальным ростом")
        elif svd_intent == "distributing":
            explanation.append("📉 УМНЫЕ ДЕНЬГИ РАСПРЕДЕЛЯЮТ:")
            explanation.append("• Крупные игроки продают, не показывая агрессию")
            explanation.append(f"• Дельта (краткосрочно): {delta:+.2f} — текущий перевес продаж")
            explanation.append(f"• CVD (накопительная): {cvd:+.2f} — общий тренд распределения")
            slope_desc = 'падает' if cvd_slope < 0 else 'растёт' if cvd_slope > 0 else 'стабильна'
            explanation.append(f"• CVD slope: {cvd_slope:+.2f} — дельта {slope_desc}")
            if is_pullback and cvd_slope > 0:
                explanation.append("• ⚠️ Краткосрочный отскок в распределении (возможны 2 сценария)")
            if direction == "down":
                explanation.append("• Ликвидность снизу — готовятся тянуть цену к стопам продавцов")
            explanation.append("• Цель: выгрузить позиции перед снижением")
        else:
            explanation.append("❓ Намерения умных денег неясны")
            explanation.append(f"• Дельта (краткосрочно): {delta:+.2f}")
            explanation.append(f"• CVD (накопительная): {cvd:+.2f}")

        # Поглощение
        if absorption.get("absorbing"):
            side = absorption.get("side", "unknown")
            explanation.append(f"\n🛡️ ПОГЛОЩЕНИЕ ({side}):")
            explanation.append("• Крупные заявки поглощают маркет-ордера противоположной стороны")
            explanation.append("• Цена стоит на месте — признак удержания/манипуляции")

        # Манипуляции / ловушки
        manip = []
        if dom.get("side") == "bid":
            manip.append("DOM дисбаланс в покупках — поддержка снизу")
        if dom.get("side") == "ask":
            manip.append("DOM дисбаланс в продажах — давление сверху")
        if thin.get("thin_above"):
            manip.append("Сверху тонкая ликвидность — возможен быстрый шип вверх")
        if thin.get("thin_below"):
            manip.append("Снизу тонкая ликвидность — возможен быстрый шип вниз")
        if spoof.get("side") or spoof_confirmed:
            side = spoof.get("side", "unknown")
            txt = f"Спуф-стенка ({side})"
            if spoof_duration:
                txt += f", жила {spoof_duration/1000:.1f}с"
            if spoof_confirmed:
                txt += " — подтверждена исчезновением без движения"
            manip.append(txt)
        if sweeps.get("sweep_up"):
            manip.append("Свип вверх — прокол хай и возврат")
        if sweeps.get("sweep_down"):
            manip.append("Свип вниз — прокол лоу и возврат")
        if sweeps.get("post_reversal"):
            manip.append("После свипа — возврат внутрь диапазона (риск реверса)")
        if fomo:
            manip.append("FOMO: ускоренный приток покупок")
        if panic:
            manip.append("Panic: ускоренный приток продаж")
        if strong_fomo:
            manip.append("Сильное FOMO: серия покупок + волатильность")
        if strong_panic:
            manip.append("Сильная паника: серия продаж + волатильность")
        manip.append(f"Фаза: {phase}")
        # Эвристика многократных отказов от верхней ликвидности и "последний свип"
        if liq_dir == "up" and dom.get("side") == "ask" and phase in ("distribution", "manipulation"):
            manip.append("Несколько тестов верхней ликвидности без закрепления — давление sell walls, риск протяжки вниз")
            manip.append("Возможен последний свип вверх (снять стопы) перед разворотом вниз")
        if liq_dir == "down" and dom.get("side") == "bid" and phase in ("accumulation", "manipulation"):
            manip.append("Несколько тестов нижней ликвидности без пробоя — bids держат, набор позиций")
            manip.append("Возможен последний свип вниз (снять стопы) перед разворотом вверх")

        if manip:
            explanation.append("\n🎭 МАНИПУЛЯЦИИ / КОНТЕКСТ:")
            for m in manip:
                explanation.append(f"• {m}")

        # Конфликты
        if (trend == "bearish" and svd_intent == "accumulating") or \
           (trend == "bullish" and svd_intent == "distributing"):
            explanation.append("\n⚠️ КОНФЛИКТ С ТРЕНДОМ:")
            explanation.append("• Действия умных денег против структуры — возможен разворот или сложная ловушка")

        # Ловушка толпы: если ликвидность против направления потока
        liq_dir = direction
        if liq_dir == "up" and svd_intent == "distributing":
            explanation.append("\n⚠️ ЛОВУШКА: Ликвидность сверху, но поток вниз — возможный свип вверх и разворот вниз")
        if liq_dir == "down" and svd_intent == "accumulating":
            explanation.append("\n⚠️ ЛОВУШКА: Ликвидность снизу, но поток вверх — возможный свип вниз и разворот вверх")

        return "\n".join(explanation)

    def generate_scenarios(self, liquidity_analysis, structure_data, svd_data, forecast):
        """
        Генерация сценариев развития событий
        """
        scenarios = []
        
        direction = liquidity_analysis.get("direction", {}).get("direction", "neutral")
        trend = structure_data.get("trend", "range")
        svd_intent = svd_data.get("intent", "unclear")
        short_term = forecast.get("short_term", {})
        long_term = forecast.get("long_term", {})

        # Сценарий 1: Движение к ближайшей ликвидности
        if short_term:
            scenarios.append({
                "name": "Краткосрочный сценарий",
                "probability": short_term.get("probability", "medium"),
                "description": f"Цена движется {short_term.get('direction', '')} к уровню ${short_term.get('target', 0):.2f}",
                "reason": short_term.get("reason", ""),
                "target": short_term.get("target", 0),
                "timeframe": "1-4 часа"
            })

        # Сценарий 2: Глобальное движение
        if long_term:
            scenarios.append({
                "name": "Глобальный сценарий",
                "probability": long_term.get("probability", "medium"),
                "description": f"Движение к {long_term.get('direction', '')} к ${long_term.get('target', 0):.2f}",
                "reason": long_term.get("reason", ""),
                "target": long_term.get("target", 0),
                "timeframe": "1-7 дней"
            })

        # Сценарий 3: На основе намерений умных денег
        if svd_intent == "accumulating" and direction == "up":
            scenarios.append({
                "name": "Сценарий накопления",
                "probability": "high",
                "description": "Умные деньги накапливают позиции, готовятся к росту",
                "reason": "Накопление + ликвидность вверх = подготовка к движению вверх",
                "target": "ближайший swing high или ATH",
                "timeframe": "2-5 дней"
            })
        elif svd_intent == "distributing" and direction == "down":
            scenarios.append({
                "name": "Сценарий распределения",
                "probability": "high",
                "description": "Умные деньги распределяют позиции, готовятся к падению",
                "reason": "Распределение + ликвидность вниз = подготовка к движению вниз",
                "target": "ближайший swing low или ATL",
                "timeframe": "2-5 дней"
            })

        # Сценарий 4: Боковик
        if trend == "range":
            range_info = structure_data.get("range", {})
            if range_info.get("in_range"):
                scenarios.append({
                    "name": "Боковой диапазон",
                    "probability": "high",
                    "description": f"Рынок в диапазоне ${range_info.get('bottom', 0):.2f} - ${range_info.get('top', 0):.2f}",
                    "reason": "Нет четкого направления, ожидание пробоя",
                    "target": "границы диапазона",
                    "timeframe": "текущий"
                })

        return scenarios

    def generate_actionable_recommendations(self, decision_result, svd_data, liquidity_data, structure_data, current_price):
        """
        Генерация практических рекомендаций "Что делать сейчас"
        """
        recommendations = []
        
        signal = decision_result.get("signal", "WAIT")
        confidence = decision_result.get("confidence", 0)
        phase = svd_data.get("phase", "discovery")
        trap_data = decision_result.get("trap", {})
        behavior_data = decision_result.get("behavior", {})
        
        svd_intent = svd_data.get("intent", "unclear")
        cvd_value = svd_data.get("cvd", 0)
        cvd_slope = svd_data.get("cvd_slope", 0)
        absorption = svd_data.get("absorption", {})
        spoof_confirmed = svd_data.get("spoof_confirmed", False)
        sweeps = liquidity_data.get("sweeps", {})
        
        # Определяем nearest liquidity
        liq_analysis = self.analyze_liquidity_zones(liquidity_data, structure_data, current_price)
        nearest_above = liq_analysis["above_price"][0] if liq_analysis["above_price"] else None
        nearest_below = liq_analysis["below_price"][0] if liq_analysis["below_price"] else None
        
        # === Рекомендации на основе сигнала и фазы ===
        
        if signal == "WAIT":
            # Вариант 1: Ждать фазу execution
            if phase in ("manipulation", "discovery"):
                recommendations.append({
                    "variant": "1",
                    "title": "Ждать фазу execution",
                    "points": [
                        "Когда фаза сменится на execution - confidence вырастет",
                        "Trap Engine даст более чёткий сигнал",
                        f"Сейчас фаза: {phase} (манипуляция/поиск ликвидности)"
                    ]
                })
            
            # Вариант 2: Два сценария движения (свип или прямой ход)
            is_pullback = svd_data.get("is_pullback_or_bounce", False)
            if (nearest_above or nearest_below) and is_pullback:
                # При pullback - показываем ОБА сценария
                scenario_points = ["ДВА возможных сценария:"]
                if svd_intent == "accumulating" and nearest_below:
                    scenario_points.append(f"А) Свип вниз к ${nearest_below['price']:.2f} → разворот вверх (вероятность ~40%)")
                    scenario_points.append(f"Б) Прямой рост без свипа (накопление завершено, вероятность ~40%)")
                    scenario_points.append("В) Боковик/ожидание (вероятность ~20%)")
                elif svd_intent == "distributing" and nearest_above:
                    scenario_points.append(f"А) Свип вверх к ${nearest_above['price']:.2f} → разворот вниз (вероятность ~40%)")
                    scenario_points.append(f"Б) Прямое падение без свипа (распределение завершено, вероятность ~40%)")
                    scenario_points.append("В) Боковик/ожидание (вероятность ~20%)")
                
                recommendations.append({
                    "variant": "2",
                    "title": "Два сценария движения",
                    "points": scenario_points
                })
            elif nearest_above or nearest_below:
                # Обычный сценарий свипа
                sweep_recommendations = [
                    "⚠️ НЕ ТОРГОВАТЬ СЕЙЧАС! Ждать подтверждения свипа:",
                    ""
                ]
                if svd_intent == "distributing" and nearest_above:
                    # Киты распределяют - ожидаем свип вверх + разворот
                    sweep_recommendations.append(
                        f"Киты распределяют → ожидается свип UP к ${nearest_above['price']:.2f}"
                    )
                    sweep_recommendations.append(
                        f"⚠️ НЕ ПОКУПАТЬ на росте! Это ловушка (bull trap)"
                    )
                    sweep_recommendations.append(
                        f"✅ SELL если: свип вверх к ${nearest_above['price']:.2f} + быстрый возврат + CVD падает"
                    )
                elif svd_intent == "accumulating" and nearest_below:
                    # Киты накапливают - ожидаем свип вниз + разворот
                    sweep_recommendations.append(
                        f"Киты накапливают → ожидается свип DOWN к ${nearest_below['price']:.2f}"
                    )
                    sweep_recommendations.append(
                        f"⚠️ НЕ ПРОДАВАТЬ на падении! Это ловушка (bear trap)"
                    )
                    sweep_recommendations.append(
                        f"✅ BUY если: свип вниз к ${nearest_below['price']:.2f} + быстрый возврат + CVD растёт"
                    )
                else:
                    # Unclear intent - общие рекомендации
                    if nearest_below:
                        sweep_recommendations.append(
                            f"Если цена свипнет вниз к ${nearest_below['price']:.2f} и быстро вернётся → BUY signal (bear trap подтверждён)"
                        )
                    if nearest_above:
                        sweep_recommendations.append(
                            f"Если цена свипнет вверх к ${nearest_above['price']:.2f} и быстро вернётся → SELL signal (bull trap подтверждён)"
                        )
                
                if spoof_confirmed:
                    spoof_side = svd_data.get("spoof_wall", {}).get("side", "unknown")
                    if spoof_side == "bid":
                        sweep_recommendations.append("Если спуф (bid) исчезнет + агрессивный селл → SELL signal")
                    elif spoof_side == "ask":
                        sweep_recommendations.append("Если спуф (ask) исчезнет + агрессивный бай → BUY signal")
                
                recommendations.append({
                    "variant": "2",
                    "title": "Следить за свипом",
                    "points": sweep_recommendations
                })
            
            # Вариант 3: Признаки реализации сценария (при pullback) или подтверждения (обычно)
            confirmation_points = []
            if is_pullback:
                # При pullback - показываем как распознать какой сценарий реализуется
                confirmation_points.append("Признаки СВИПА:")
                if svd_intent == "accumulating":
                    confirmation_points.append("• Фаза manipulation, спуф на bid, DOM chasing вниз")
                    confirmation_points.append("• Цена приближается к нижней ликвидности (< 2%)")
                else:
                    confirmation_points.append("• Фаза manipulation, спуф на ask, DOM chasing вверх")
                    confirmation_points.append("• Цена приближается к верхней ликвидности (< 2%)")
                
                confirmation_points.append("\nПризнаки ПРЯМОГО ДВИЖЕНИЯ:")
                if svd_intent == "accumulating":
                    confirmation_points.append("• CVD slope разворачивается вверх (> 0), absorption на buy")
                    confirmation_points.append("• Фаза execution, aggressive buying растёт")
                else:
                    confirmation_points.append("• CVD slope разворачивается вниз (< 0), absorption на sell")
                    confirmation_points.append("• Фаза execution, aggressive selling растёт")
            else:
                # Обычные подтверждения
                if svd_intent == "accumulating":
                    confirmation_points.append(f"CVD начнёт расти (сейчас: {cvd_value:.2f}, slope: {cvd_slope:.2f})")
                    confirmation_points.append("Absorption на buy (киты поглощают селл-ордера)")
                    if spoof_confirmed:
                        confirmation_points.append("Спуф исчезнет, но цена устоит (истинное накопление)")
                elif svd_intent == "distributing":
                    confirmation_points.append(f"CVD начнёт падать (сейчас: {cvd_value:.2f}, slope: {cvd_slope:.2f})")
                    confirmation_points.append("Absorption на sell (киты поглощают бай-ордера)")
                    if spoof_confirmed:
                        confirmation_points.append("Спуф исчезнет, и цена пойдёт вниз (истинное распределение)")
                else:
                    confirmation_points.append("Дождаться чёткого SVD intent (accumulating или distributing)")
                    confirmation_points.append("CVD подтвердит направление")
            
            if confirmation_points:
                title = "Как распознать сценарий" if is_pullback else "Дождаться подтверждений"
                recommendations.append({
                    "variant": "3",
                    "title": title,
                    "points": confirmation_points
                })
        
        elif signal == "BUY" and confidence >= 5.0:
            # Сильный BUY сигнал
            recommendations.append({
                "variant": "1",
                "title": "Готовиться к входу в лонг",
                "points": [
                    f"Confidence: {confidence:.1f}/10 - сигнал достаточно сильный",
                    f"Фаза: {phase}",
                    f"Зона входа: текущая цена (${current_price:.2f})" if current_price else "Зона входа: по уровням",
                    f"Цель: {nearest_above['price']:.2f} (+{nearest_above['distance_pct']:.2f}%)" if nearest_above else "Цель: ближайшая ликвидность выше"
                ]
            })
            recommendations.append({
                "variant": "2",
                "title": "Риск-менеджмент",
                "points": [
                    f"Стоп: ниже ${nearest_below['price']:.2f}" if nearest_below else "Стоп: ниже ближайшего swing low",
                    "Следить за изменением фазы на distribution (сигнал к выходу)",
                    "Если CVD начнёт падать - уменьшить позицию"
                ]
            })
        
        elif signal == "BUY" and confidence < 5.0:
            # Слабый BUY сигнал
            recommendations.append({
                "variant": "1",
                "title": "Подождать усиления сигнала",
                "points": [
                    f"Confidence: {confidence:.1f}/10 - слишком низкая уверенность",
                    "Дождаться роста confidence до 5-6",
                    f"Следить за сменой фазы на execution"
                ]
            })
            recommendations.append({
                "variant": "2",
                "title": "Консервативный вход (малая позиция)",
                "points": [
                    "Войти небольшой позицией (10-20% от обычной)",
                    "Дождаться подтверждения (CVD рост, absorption на buy)",
                    "Увеличить позицию при росте confidence"
                ]
            })
        
        elif signal == "SELL" and confidence >= 5.0:
            # Сильный SELL сигнал
            recommendations.append({
                "variant": "1",
                "title": "Готовиться к входу в шорт",
                "points": [
                    f"Confidence: {confidence:.1f}/10 - сигнал достаточно сильный",
                    f"Фаза: {phase}",
                    f"Зона входа: текущая цена (${current_price:.2f})" if current_price else "Зона входа: по уровням",
                    f"Цель: {nearest_below['price']:.2f} (-{nearest_below['distance_pct']:.2f}%)" if nearest_below else "Цель: ближайшая ликвидность ниже"
                ]
            })
            recommendations.append({
                "variant": "2",
                "title": "Риск-менеджмент",
                "points": [
                    f"Стоп: выше ${nearest_above['price']:.2f}" if nearest_above else "Стоп: выше ближайшего swing high",
                    "Следить за изменением фазы на execution вверх (сигнал к выходу)",
                    "Если CVD начнёт расти - уменьшить позицию"
                ]
            })
        
        elif signal == "SELL" and confidence < 5.0:
            # Слабый SELL сигнал
            recommendations.append({
                "variant": "1",
                "title": "Подождать усиления сигнала",
                "points": [
                    f"Confidence: {confidence:.1f}/10 - слишком низкая уверенность",
                    "Дождаться роста confidence до 5-6",
                    f"Следить за сменой фазы на execution"
                ]
            })
            recommendations.append({
                "variant": "2",
                "title": "Консервативный вход (малая позиция)",
                "points": [
                    "Войти небольшой позицией (10-20% от обычной)",
                    "Дождаться подтверждения (CVD падение, absorption на sell)",
                    "Увеличить позицию при росте confidence"
                ]
            })
        
        # Дополнительные рекомендации на основе trap
        if trap_data.get("is_trap"):
            trap_type = trap_data.get("trap_type")
            expected_reversal = trap_data.get("expected_reversal_direction")
            recommendations.append({
                "variant": "⚠️",
                "title": f"ЛОВУШКА: {trap_type}",
                "points": [
                    f"Trap Engine обнаружил {trap_type}",
                    f"Ожидается разворот: {expected_reversal}",
                    "Не входить против ожидаемого разворота",
                    "Дождаться подтверждения trap через свип"
                ]
            })
        
        return recommendations

    def generate_full_report(self, liquidity_data, structure_data, svd_data, ta_data, current_price, decision_result=None):
        """
        Генерация полного глубокого отчета
        """
        # Анализ ликвидности
        liquidity_analysis = self.analyze_liquidity_zones(liquidity_data, structure_data, current_price)
        
        # Прогноз движения
        forecast = self.generate_price_movement_forecast(
            liquidity_data, structure_data, svd_data, current_price, liquidity_analysis
        )
        
        # Действия умных денег
        smart_money = self.explain_smart_money_actions(svd_data, liquidity_data, structure_data)
        
        # Сценарии
        scenarios = self.generate_scenarios(liquidity_analysis, structure_data, svd_data, forecast)
        
        # Практические рекомендации
        recommendations = []
        if decision_result:
            recommendations = self.generate_actionable_recommendations(
                decision_result, svd_data, liquidity_data, structure_data, current_price
            )

        return {
            "liquidity_analysis": liquidity_analysis,
            "forecast": forecast,
            "smart_money": smart_money,
            "scenarios": scenarios,
            "recommendations": recommendations
        }

