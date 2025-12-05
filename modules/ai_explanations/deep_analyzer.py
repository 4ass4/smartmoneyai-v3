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
            "nearest_targets": {}
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

        return analysis

    def generate_price_movement_forecast(self, liquidity_data, structure_data, svd_data, current_price, liquidity_analysis):
        """
        Генерация прогноза движения цены к ликвидности
        """
        forecast = {
            "short_term": {},
            "long_term": {},
            "scenarios": []
        }

        direction = liquidity_data.get("direction", {}).get("direction", "neutral")
        nearest_above = liquidity_analysis.get("nearest_targets", {}).get("above")
        nearest_below = liquidity_analysis.get("nearest_targets", {}).get("below")

        # Краткосрочный прогноз (ближайшие уровни)
        if direction == "up" and nearest_above:
            forecast["short_term"] = {
                "direction": "UP",
                "target": nearest_above["price"],
                "distance_pct": nearest_above["distance_pct"],
                "reason": f"Ликвидность покупателей (buy stops) на уровне ${nearest_above['price']:.2f}",
                "probability": "high" if nearest_above["distance_pct"] < 1.0 else "medium"
            }
        elif direction == "down" and nearest_below:
            forecast["short_term"] = {
                "direction": "DOWN",
                "target": nearest_below["price"],
                "distance_pct": nearest_below["distance_pct"],
                "reason": f"Ликвидность продавцов (sell stops) на уровне ${nearest_below['price']:.2f}",
                "probability": "high" if nearest_below["distance_pct"] < 1.0 else "medium"
            }

        # Глобальный прогноз (ATH/ATL)
        ath_atl = liquidity_data.get("ath_atl", {})
        if ath_atl:
            ath = ath_atl.get("ath", {}).get("price", 0)
            atl = ath_atl.get("atl", {}).get("price", 0)
            
            if ath > current_price:
                forecast["long_term"] = {
                    "direction": "UP",
                    "target": ath,
                    "distance_pct": ((ath - current_price) / current_price) * 100,
                    "reason": f"Исторический максимум (ATH) на ${ath:.2f} - зона максимальной ликвидности",
                    "probability": "medium"
                }
            if atl < current_price:
                forecast["long_term"] = {
                    "direction": "DOWN",
                    "target": atl,
                    "distance_pct": ((current_price - atl) / current_price) * 100,
                    "reason": f"Исторический минимум (ATL) на ${atl:.2f} - зона максимальной ликвидности",
                    "probability": "medium"
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

        # Намерения
        if svd_intent == "accumulating":
            explanation.append("💰 УМНЫЕ ДЕНЬГИ НАКАПЛИВАЮТ:")
            explanation.append("• Крупные игроки постепенно покупают и скрывают интерес")
            explanation.append(f"• Дельта положительная ( +{delta:.2f} ) — перевес покупок")
            if direction == "up":
                explanation.append("• Ликвидность сверху — готовятся тянуть цену к стопам покупателей")
            explanation.append("• Цель: собрать позиции перед потенциальным ростом")
        elif svd_intent == "distributing":
            explanation.append("📉 УМНЫЕ ДЕНЬГИ РАСПРЕДЕЛЯЮТ:")
            explanation.append("• Крупные игроки продают, не показывая агрессию")
            explanation.append(f"• Дельта отрицательная ( {delta:.2f} ) — перевес продаж")
            if direction == "down":
                explanation.append("• Ликвидность снизу — готовятся тянуть цену к стопам продавцов")
            explanation.append("• Цель: выгрузить позиции перед снижением")
        else:
            explanation.append("❓ Намерения умных денег неясны, дельта слабая")

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

    def generate_full_report(self, liquidity_data, structure_data, svd_data, ta_data, current_price):
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

        return {
            "liquidity_analysis": liquidity_analysis,
            "forecast": forecast,
            "smart_money": smart_money,
            "scenarios": scenarios
        }

