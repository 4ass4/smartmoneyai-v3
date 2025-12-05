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
        Объяснение действий умных денег
        """
        explanation = []
        
        svd_intent = svd_data.get("intent", "unclear")
        delta = svd_data.get("delta", 0)
        absorption = svd_data.get("absorption", {})
        direction = liquidity_data.get("direction", {}).get("direction", "neutral")
        trend = structure_data.get("trend", "range")

        # Анализ намерений
        if svd_intent == "accumulating":
            explanation.append("💰 УМНЫЕ ДЕНЬГИ НАКАПЛИВАЮТ:")
            explanation.append("• Крупные игроки покупают позиции, маскируя это под обычную торговлю")
            explanation.append("• Дельта положительная - больше покупок чем продаж")
            if direction == "up":
                explanation.append("• Ликвидность указывает вверх - готовятся к движению вверх")
            explanation.append("• Цель: собрать позиции перед ростом")
        elif svd_intent == "distributing":
            explanation.append("📉 УМНЫЕ ДЕНЬГИ РАСПРЕДЕЛЯЮТ:")
            explanation.append("• Крупные игроки продают позиции, не показывая агрессию")
            explanation.append("• Дельта отрицательная - больше продаж чем покупок")
            if direction == "down":
                explanation.append("• Ликвидность указывает вниз - готовятся к движению вниз")
            explanation.append("• Цель: выгрузить позиции перед падением")

        # Поглощение
        if absorption.get("absorbing"):
            side = absorption.get("side", "")
            explanation.append(f"\n🛡️ ОБНАРУЖЕНО ПОГЛОЩЕНИЕ ({side}):")
            explanation.append("• Крупные игроки поглощают маркет-ордера противоположной стороны")
            explanation.append("• Цена не двигается несмотря на объем - это признак манипуляции")
            explanation.append("• Умные деньги контролируют цену")

        # Конфликты
        if (trend == "bearish" and svd_intent == "accumulating") or \
           (trend == "bullish" and svd_intent == "distributing"):
            explanation.append("\n⚠️ КОНФЛИКТ СИГНАЛОВ:")
            explanation.append("• Структура рынка противоречит действиям умных денег")
            explanation.append("• Возможен разворот или продолжение тренда после накопления/распределения")

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

