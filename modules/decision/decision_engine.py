# modules/decision/decision_engine.py

from .risk_filters import apply_risk_filters


class DecisionEngine:
    """
    Decision Engine v3.0
    Финальный блок, объединяющий все модули и принимающий решение
    """

    def __init__(self, config=None):
        self.config = config
        self.min_confidence = 7.0 if config is None else getattr(config, 'MIN_CONFIDENCE', 7.0)

    def analyze(self, liquidity_data, svd_data, market_structure, ta_data, current_price=None):
        """
        Главный метод принятия решения
        
        Args:
            liquidity_data: данные от LiquidityEngine
            svd_data: данные от SVDEngine
            market_structure: данные от MarketStructureEngine
            ta_data: данные от TAEngine
            current_price: текущая цена (опционально)
            
        Returns:
            Dict с финальным сигналом и объяснением
        """
        # Сбор всех сигналов
        signals = {
            "liquidity": liquidity_data,
            "svd": svd_data,
            "structure": market_structure,
            "ta": ta_data,
            "current_price": current_price
        }
        
        # Определение направления
        direction = self._determine_direction(signals)
        
        # Расчет confidence
        confidence = self._calculate_confidence(signals)
        
        # Применение фильтров риска
        filtered = apply_risk_filters(signals, confidence)
        
        if not filtered["allowed"]:
            return {
                "signal": "WAIT",
                "confidence": 0,
                "reason": filtered["reason"],
                "explanation": filtered["reason"]
            }
        
        # Генерация объяснения
        explanation = self._generate_explanation(signals, direction, confidence)
        
        # Добавляем current_price в signals для расчета уровней
        if current_price is not None:
            signals["current_price"] = current_price
        
        # Определение уровней
        levels = self._calculate_levels(signals)
        
        return {
            "signal": direction,
            "confidence": confidence,
            "explanation": explanation,
            "scenario": {
                "main": explanation,
                "alternative": self._generate_alternative_scenario(signals)
            },
            "levels": levels
        }
    
    def _determine_direction(self, signals):
        """Определяет финальное направление на основе всех сигналов"""
        votes = {"BUY": 0, "SELL": 0, "WAIT": 0}
        
        # Liquidity
        liq_dir = signals["liquidity"].get("direction", {}).get("direction", "neutral")
        if liq_dir == "up":
            votes["BUY"] += 2
        elif liq_dir == "down":
            votes["SELL"] += 2
        
        # SVD
        svd_intent = signals["svd"].get("intent", "unclear")
        if svd_intent == "accumulating":
            votes["BUY"] += 1
        elif svd_intent == "distributing":
            votes["SELL"] += 1
        
        # Market Structure
        trend = signals["structure"].get("trend", "range")
        if trend == "bullish":
            votes["BUY"] += 1
        elif trend == "bearish":
            votes["SELL"] += 1
        
        # TA
        ta_trend = signals["ta"].get("trend", "neutral")
        if ta_trend == "bullish":
            votes["BUY"] += 1
        elif ta_trend == "bearish":
            votes["SELL"] += 1
        
        # Определение победителя
        max_votes = max(votes.values())
        if max_votes == 0:
            return "WAIT"
        
        for signal, count in votes.items():
            if count == max_votes:
                return signal
        
        return "WAIT"
    
    def _calculate_confidence(self, signals):
        """Рассчитывает итоговый confidence (0-10)"""
        scores = []
        
        # Liquidity confidence (если есть)
        if "confidence" in signals["liquidity"]:
            scores.append(signals["liquidity"]["confidence"])
        
        # SVD confidence
        if "confidence" in signals["svd"]:
            svd_conf = signals["svd"]["confidence"]
            if svd_conf > 0:
                scores.append(svd_conf)
        
        # Оцениваем по согласованности сигналов
        liq_dir = signals["liquidity"].get("direction", {}).get("direction", "neutral")
        svd_intent = signals["svd"].get("intent", "unclear")
        trend = signals["structure"].get("trend", "range")
        ta_trend = signals["ta"].get("trend", "neutral")
        
        agreement = 0
        # Согласованность Liquidity и SVD
        if (liq_dir == "up" and svd_intent == "accumulating") or \
           (liq_dir == "down" and svd_intent == "distributing"):
            agreement += 2
        
        # Согласованность Structure и Liquidity
        if (trend == "bullish" and liq_dir == "up") or \
           (trend == "bearish" and liq_dir == "down"):
            agreement += 2
        elif trend == "range":
            agreement += 1
        
        # Согласованность TA и Structure
        if ta_trend == trend:
            agreement += 1
        
        # Базовый confidence от согласованности
        base_confidence = min(agreement * 1.5, 6)
        
        # Если есть confidence от модулей, усредняем
        if scores:
            avg_confidence = sum(scores) / len(scores)
            # Комбинируем: 60% от модулей, 40% от согласованности
            final_confidence = (avg_confidence * 0.6) + (base_confidence * 0.4)
        else:
            final_confidence = base_confidence
        
        return min(final_confidence, 10)
    
    def _generate_explanation(self, signals, direction, confidence):
        """Генерирует объяснение на русском с учетом реальных данных"""
        parts = []
        
        liq_dir = signals["liquidity"].get("direction", {}).get("direction", "neutral")
        svd_intent = signals["svd"].get("intent", "unclear")
        trend = signals["structure"].get("trend", "range")
        delta = signals["svd"].get("delta", 0)
        absorption = signals["svd"].get("absorption", {})
        
        if direction == "BUY":
            parts.append("Сигнал на покупку")
            if liq_dir == "up":
                parts.append("ликвидность указывает на движение вверх")
            # Используем реальные данные SVD
            if svd_intent == "accumulating":
                parts.append("крупные игроки накапливают позиции")
            elif svd_intent == "distributing":
                parts.append("⚠️ ВНИМАНИЕ: крупные игроки распределяют позиции (противоречие с сигналом)")
            if absorption.get("absorbing"):
                parts.append(f"обнаружено поглощение ({absorption.get('side', 'unknown')})")
        elif direction == "SELL":
            parts.append("Сигнал на продажу")
            if liq_dir == "down":
                parts.append("ликвидность указывает на движение вниз")
            # Используем реальные данные SVD
            if svd_intent == "distributing":
                parts.append("крупные игроки распределяют позиции")
            elif svd_intent == "accumulating":
                parts.append("⚠️ ВНИМАНИЕ: крупные игроки накапливают позиции (противоречие с сигналом)")
            if absorption.get("absorbing"):
                parts.append(f"обнаружено поглощение ({absorption.get('side', 'unknown')})")
        else:
            return "Недостаточно сигналов для принятия решения. Рекомендуется ожидание."
        
        return ". ".join(parts) + f" (уверенность: {confidence:.1f}/10)"
    
    def _generate_alternative_scenario(self, signals):
        """Генерирует альтернативный сценарий"""
        return "Если произойдет разворот структуры рынка, сигнал может измениться."
    
    def _calculate_levels(self, signals):
        """Рассчитывает уровни входа, целей и стоп-лосса на основе реальных данных"""
        levels = {
            "entry_zone": None,
            "targets": [],
            "invalidation": None
        }
        
        # Получаем данные
        liquidity_data = signals.get("liquidity", {})
        structure_data = signals.get("structure", {})
        direction = signals.get("signal", "WAIT")
        current_price = signals.get("current_price")  # Текущая цена
        
        # Находим ближайшие уровни ликвидности
        stop_clusters = liquidity_data.get("stop_clusters", [])
        swing_liq = liquidity_data.get("swing_liquidity", [])
        
        # Получаем swing points
        swings = structure_data.get("swings", {})
        highs = swings.get("highs", [])
        lows = swings.get("lows", [])
        
        # Если нет текущей цены, пытаемся получить из последней свечи или swing
        if current_price is None:
            if highs and lows:
                # Используем среднее между последним high и low
                last_high = highs[-1]["price"] if highs else 0
                last_low = lows[-1]["price"] if lows else 0
                current_price = (last_high + last_low) / 2 if (last_high > 0 and last_low > 0) else None
        
        # Определяем ближайшие уровни
        if direction == "BUY":
            targets = []
            
            # 1. Ищем ближайшие buy_stops выше текущей цены (приоритет)
            above_stops = []
            for cluster in stop_clusters:
                if cluster.get("type") == "buy_stops":
                    price = cluster.get("price", 0)
                    if price > 0 and (current_price is None or price > current_price):
                        above_stops.append(price)
            
            if above_stops:
                above_stops.sort()
                targets.append(f"${above_stops[0]:.2f}")  # Ближайшая цель
                if len(above_stops) > 1:
                    targets.append(f"${above_stops[1]:.2f}")  # Вторая цель
            
            # 2. Если нет стопов, используем swing highs выше цены
            if not targets and highs:
                above_highs = [s["price"] for s in highs if s.get("price", 0) > 0 and (current_price is None or s["price"] > current_price)]
                if above_highs:
                    above_highs.sort()
                    targets.append(f"${above_highs[0]:.2f}")
                    if len(above_highs) > 1:
                        targets.append(f"${above_highs[1]:.2f}")
            
            # 3. Если все еще нет, используем swing liquidity
            if not targets and swing_liq:
                above_swing = [s.get("price", 0) for s in swing_liq if s.get("type") == "buy_stops" and s.get("price", 0) > 0 and (current_price is None or s.get("price", 0) > current_price)]
                if above_swing:
                    above_swing.sort()
                    targets.append(f"${above_swing[0]:.2f}")
            
            # 4. Последний вариант - ATH
            if not targets:
                ath_atl = liquidity_data.get("ath_atl", {})
                if ath_atl.get("ath", {}).get("price"):
                    ath_price = ath_atl["ath"]["price"]
                    if current_price is None or ath_price > current_price:
                        targets.append(f"${ath_price:.2f} (ATH)")
            
            levels["targets"] = targets
            
            # Зона входа - текущая цена или ближайший swing low
            if current_price:
                if lows:
                    nearest_low = max([s["price"] for s in lows if s.get("price", 0) > 0 and s["price"] < current_price], default=None)
                    if nearest_low:
                        levels["entry_zone"] = f"${nearest_low:.2f} - ${current_price:.2f}"
                    else:
                        levels["entry_zone"] = f"${current_price:.2f}"
                else:
                    levels["entry_zone"] = f"${current_price:.2f}"
            
            # Стоп - ниже ближайшего swing low
            if lows:
                below_lows = [s["price"] for s in lows if s.get("price", 0) > 0]
                if below_lows:
                    min_low = min(below_lows)
                    levels["invalidation"] = f"${min_low * 0.998:.2f}"  # -0.2% от swing low
            
        elif direction == "SELL":
            targets = []
            
            # 1. Ищем ближайшие sell_stops ниже текущей цены (приоритет)
            below_stops = []
            for cluster in stop_clusters:
                if cluster.get("type") == "sell_stops":
                    price = cluster.get("price", 0)
                    if price > 0 and (current_price is None or price < current_price):
                        below_stops.append(price)
            
            if below_stops:
                below_stops.sort(reverse=True)
                targets.append(f"${below_stops[0]:.2f}")  # Ближайшая цель
                if len(below_stops) > 1:
                    targets.append(f"${below_stops[1]:.2f}")  # Вторая цель
            
            # 2. Если нет стопов, используем swing lows ниже цены
            if not targets and lows:
                below_lows = [s["price"] for s in lows if s.get("price", 0) > 0 and (current_price is None or s["price"] < current_price)]
                if below_lows:
                    below_lows.sort(reverse=True)
                    targets.append(f"${below_lows[0]:.2f}")
                    if len(below_lows) > 1:
                        targets.append(f"${below_lows[1]:.2f}")
            
            # 3. Если все еще нет, используем swing liquidity
            if not targets and swing_liq:
                below_swing = [s.get("price", 0) for s in swing_liq if s.get("type") == "sell_stops" and s.get("price", 0) > 0 and (current_price is None or s.get("price", 0) < current_price)]
                if below_swing:
                    below_swing.sort(reverse=True)
                    targets.append(f"${below_swing[0]:.2f}")
            
            # 4. Последний вариант - ATL
            if not targets:
                ath_atl = liquidity_data.get("ath_atl", {})
                if ath_atl.get("atl", {}).get("price"):
                    atl_price = ath_atl["atl"]["price"]
                    if current_price is None or atl_price < current_price:
                        targets.append(f"${atl_price:.2f} (ATL)")
            
            levels["targets"] = targets
            
            # Зона входа - текущая цена или ближайший swing high
            if current_price:
                if highs:
                    nearest_high = min([s["price"] for s in highs if s.get("price", 0) > 0 and s["price"] > current_price], default=None)
                    if nearest_high:
                        levels["entry_zone"] = f"${current_price:.2f} - ${nearest_high:.2f}"
                    else:
                        levels["entry_zone"] = f"${current_price:.2f}"
                else:
                    levels["entry_zone"] = f"${current_price:.2f}"
            
            # Стоп - выше ближайшего swing high
            if highs:
                above_highs = [s["price"] for s in highs if s.get("price", 0) > 0]
                if above_highs:
                    max_high = max(above_highs)
                    levels["invalidation"] = f"${max_high * 1.002:.2f}"  # +0.2% от swing high
        
        # Очищаем пустые значения
        if not levels["entry_zone"]:
            levels.pop("entry_zone", None)
        if not levels["targets"]:
            levels.pop("targets", None)
        if not levels["invalidation"]:
            levels.pop("invalidation", None)
        
        return levels

