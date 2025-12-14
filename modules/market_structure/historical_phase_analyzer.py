# modules/market_structure/historical_phase_analyzer.py

"""
Анализатор исторических фаз накопления/распределения на HTF
Отслеживает глобальные тренды формирования позиций китов
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class HistoricalPhaseAnalyzer:
    """
    Анализирует исторические фазы накопления/распределения на больших таймфреймах
    """
    
    def __init__(self):
        pass
    
    def analyze_historical_phases(self, df, timeframe_name="HTF"):
        """
        Анализирует исторические фазы накопления/распределения
        
        Args:
            df: OHLCV DataFrame (HTF: 1h, 4h, 1d)
            timeframe_name: название таймфрейма для логов
        
        Returns:
            dict: {
                "global_trend": "accumulation" | "distribution" | "neutral",
                "trend_strength": 0.0-1.0,
                "phase_history": [
                    {"phase": "accumulation", "start": timestamp, "end": timestamp, "duration_hours": float, "price_range": (low, high)},
                    ...
                ],
                "current_phase": "accumulation" | "distribution",
                "current_phase_duration_hours": float,
                "accumulation_zones": [(price_low, price_high, volume_sum), ...],
                "distribution_zones": [(price_low, price_high, volume_sum), ...],
                "trend_consistency": 0.0-1.0  # Насколько последователен тренд
            }
        """
        if df is None or len(df) < 20:
            return {
                "global_trend": "neutral",
                "trend_strength": 0.0,
                "phase_history": [],
                "current_phase": "neutral",
                "current_phase_duration_hours": 0,
                "accumulation_zones": [],
                "distribution_zones": [],
                "trend_consistency": 0.0
            }
        
        # 1. Определяем фазы на основе объёма и цены
        phases = self._detect_phases_from_volume_price(df)
        
        # 2. Анализируем историю фаз
        phase_history = self._build_phase_history(df, phases)
        
        # 3. Определяем глобальный тренд
        global_trend, trend_strength = self._determine_global_trend(phase_history, df)
        
        # 4. Текущая фаза
        current_phase, current_duration = self._get_current_phase(phase_history, df)
        
        # 5. Зоны накопления/распределения
        accumulation_zones, distribution_zones = self._identify_zones(df, phases)
        
        # 6. Консистентность тренда
        trend_consistency = self._calculate_trend_consistency(phase_history)
        
        result = {
            "global_trend": global_trend,
            "trend_strength": trend_strength,
            "phase_history": phase_history,
            "current_phase": current_phase,
            "current_phase_duration_hours": current_duration,
            "accumulation_zones": accumulation_zones,
            "distribution_zones": distribution_zones,
            "trend_consistency": trend_consistency
        }
        
        logger.info(f"📊 {timeframe_name} Historical Phases: {global_trend} (strength: {trend_strength:.2f}, "
                   f"current: {current_phase}, duration: {current_duration:.1f}h)")
        
        return result
    
    def _detect_phases_from_volume_price(self, df):
        """
        Определяет фазы на основе объёма и движения цены
        
        Логика:
        - Accumulation: высокий объём + боковое движение или медленный рост
        - Distribution: высокий объём + боковое движение или медленное падение
        - Execution: сильное движение цены с объёмом
        """
        phases = []
        
        # Скользящие средние для объёма и цены
        volume_ma = df['volume'].rolling(window=10).mean()
        price_ma = df['close'].rolling(window=10).mean()
        
        # Определяем волатильность
        price_volatility = df['close'].rolling(window=10).std()
        avg_volatility = price_volatility.mean()
        
        for i in range(10, len(df)):
            window = df.iloc[i-10:i+1]
            current = df.iloc[i]
            
            # Средний объём за окно
            avg_volume = window['volume'].mean()
            current_volume = current['volume']
            
            # Изменение цены за окно
            price_change = (current['close'] - window['close'].iloc[0]) / window['close'].iloc[0] * 100
            price_range = (window['high'].max() - window['low'].min()) / window['close'].iloc[0] * 100
            
            # Определяем фазу
            if current_volume > avg_volume * 1.2:  # Высокий объём
                if abs(price_change) < 2.0 and price_range < 3.0:  # Боковое движение
                    # Накопление или распределение
                    if price_change > 0:
                        phase = "accumulation"
                    else:
                        phase = "distribution"
                elif price_change > 3.0:  # Сильный рост
                    phase = "execution_up"
                elif price_change < -3.0:  # Сильное падение
                    phase = "execution_down"
                else:
                    phase = "neutral"
            else:
                phase = "neutral"
            
            phases.append({
                "index": i,
                "phase": phase,
                "timestamp": current.name if hasattr(current.name, '__iter__') else i,
                "price": current['close'],
                "volume": current_volume,
                "price_change_pct": price_change
            })
        
        return phases
    
    def _build_phase_history(self, df, phases):
        """
        Строит историю фаз с длительностью и ценовыми диапазонами
        """
        if not phases:
            return []
        
        history = []
        current_phase = None
        phase_start_idx = None
        phase_start_price = None
        
        for phase_data in phases:
            phase = phase_data["phase"]
            
            if phase != current_phase:
                # Завершаем предыдущую фазу
                if current_phase and phase_start_idx is not None:
                    phase_window = df.iloc[phase_start_idx:phase_data["index"]]
                    duration_candles = phase_data["index"] - phase_start_idx
                    
                    # Определяем длительность в часах (зависит от таймфрейма)
                    # Для 1h: 1 candle = 1 hour, для 4h: 1 candle = 4 hours
                    timeframe_hours = self._estimate_timeframe_hours(df, phase_start_idx, phase_data["index"])
                    duration_hours = duration_candles * timeframe_hours
                    
                    history.append({
                        "phase": current_phase,
                        "start_index": phase_start_idx,
                        "end_index": phase_data["index"],
                        "start_price": phase_start_price,
                        "end_price": phase_data["price"],
                        "duration_candles": duration_candles,
                        "duration_hours": duration_hours,
                        "price_range": (phase_window['low'].min(), phase_window['high'].max()),
                        "volume_sum": phase_window['volume'].sum()
                    })
                
                # Начинаем новую фазу
                current_phase = phase
                phase_start_idx = phase_data["index"]
                phase_start_price = phase_data["price"]
        
        # Добавляем последнюю фазу (если она ещё не завершена)
        if current_phase and phase_start_idx is not None:
            last_idx = len(df) - 1
            phase_window = df.iloc[phase_start_idx:]
            duration_candles = last_idx - phase_start_idx + 1
            timeframe_hours = self._estimate_timeframe_hours(df, phase_start_idx, last_idx)
            duration_hours = duration_candles * timeframe_hours
            
            history.append({
                "phase": current_phase,
                "start_index": phase_start_idx,
                "end_index": last_idx,
                "start_price": phase_start_price,
                "end_price": df['close'].iloc[-1],
                "duration_candles": duration_candles,
                "duration_hours": duration_hours,
                "price_range": (phase_window['low'].min(), phase_window['high'].max()),
                "volume_sum": phase_window['volume'].sum(),
                "is_active": True  # Текущая активная фаза
            })
        
        return history
    
    def _estimate_timeframe_hours(self, df, start_idx, end_idx):
        """
        Оценивает длительность одного свечи в часах
        """
        if len(df) < 2:
            return 1.0
        
        # Пробуем определить по timestamp если есть
        if hasattr(df.index, 'dtype'):
            try:
                if pd.api.types.is_datetime64_any_dtype(df.index):
                    if end_idx > start_idx:
                        time_diff = df.index[end_idx] - df.index[start_idx]
                        hours = time_diff.total_seconds() / 3600 / (end_idx - start_idx)
                        return max(0.25, min(24, hours))  # От 15 минут до 24 часов
            except:
                pass
        
        # Fallback: оцениваем по количеству свечей
        # Если 200 свечей за ~33 дня (4h) → 1 свеча = 4 часа
        # Если 200 свечей за ~8 дней (1h) → 1 свеча = 1 час
        total_candles = len(df)
        if total_candles > 100:
            # Предполагаем что это HTF (1h или 4h)
            # Для 1h: 200 свечей = 8.3 дня = 200 часов
            # Для 4h: 200 свечей = 33 дня = 800 часов
            estimated_days = total_candles / 24  # Если 1h
            if estimated_days > 20:  # Если больше 20 дней → вероятно 4h
                return 4.0
            else:
                return 1.0
        
        return 1.0  # По умолчанию 1 час
    
    def _determine_global_trend(self, phase_history, df):
        """
        Определяет глобальный тренд на основе истории фаз
        """
        if not phase_history:
            return "neutral", 0.0
        
        # Подсчитываем время в каждой фазе
        accumulation_time = 0
        distribution_time = 0
        execution_up_time = 0
        execution_down_time = 0
        
        for phase_data in phase_history:
            duration = phase_data.get("duration_hours", 0)
            phase = phase_data["phase"]
            
            if phase == "accumulation":
                accumulation_time += duration
            elif phase == "distribution":
                distribution_time += duration
            elif phase == "execution_up":
                execution_up_time += duration
            elif phase == "execution_down":
                execution_down_time += duration
        
        total_time = accumulation_time + distribution_time + execution_up_time + execution_down_time
        
        if total_time == 0:
            return "neutral", 0.0
        
        # Определяем доминирующий тренд
        accumulation_ratio = (accumulation_time + execution_up_time) / total_time
        distribution_ratio = (distribution_time + execution_down_time) / total_time
        
        if accumulation_ratio > 0.6:
            global_trend = "accumulation"
            trend_strength = min(1.0, accumulation_ratio)
        elif distribution_ratio > 0.6:
            global_trend = "distribution"
            trend_strength = min(1.0, distribution_ratio)
        else:
            global_trend = "neutral"
            trend_strength = abs(accumulation_ratio - distribution_ratio)
        
        return global_trend, trend_strength
    
    def _get_current_phase(self, phase_history, df):
        """
        Получает текущую активную фазу
        """
        if not phase_history:
            return "neutral", 0.0
        
        # Ищем активную фазу
        for phase_data in reversed(phase_history):
            if phase_data.get("is_active", False):
                return phase_data["phase"], phase_data.get("duration_hours", 0.0)
        
        # Если нет активной, берём последнюю
        if phase_history:
            last = phase_history[-1]
            return last["phase"], last.get("duration_hours", 0.0)
        
        return "neutral", 0.0
    
    def _identify_zones(self, df, phases):
        """
        Идентифицирует зоны накопления и распределения
        """
        accumulation_zones = []
        distribution_zones = []
        
        current_zone = None
        zone_start_idx = None
        
        for phase_data in phases:
            phase = phase_data["phase"]
            
            if phase in ("accumulation", "distribution"):
                if current_zone != phase:
                    # Завершаем предыдущую зону
                    if current_zone and zone_start_idx is not None:
                        zone_window = df.iloc[zone_start_idx:phase_data["index"]]
                        zone_volume = zone_window['volume'].sum()
                        zone_low = zone_window['low'].min()
                        zone_high = zone_window['high'].max()
                        
                        if current_zone == "accumulation":
                            accumulation_zones.append((zone_low, zone_high, zone_volume))
                        else:
                            distribution_zones.append((zone_low, zone_high, zone_volume))
                    
                    # Начинаем новую зону
                    current_zone = phase
                    zone_start_idx = phase_data["index"]
            else:
                # Завершаем зону если была
                if current_zone and zone_start_idx is not None:
                    zone_window = df.iloc[zone_start_idx:phase_data["index"]]
                    zone_volume = zone_window['volume'].sum()
                    zone_low = zone_window['low'].min()
                    zone_high = zone_window['high'].max()
                    
                    if current_zone == "accumulation":
                        accumulation_zones.append((zone_low, zone_high, zone_volume))
                    else:
                        distribution_zones.append((zone_low, zone_high, zone_volume))
                    
                    current_zone = None
                    zone_start_idx = None
        
        return accumulation_zones, distribution_zones
    
    def _calculate_trend_consistency(self, phase_history):
        """
        Рассчитывает консистентность тренда (насколько последовательны фазы)
        """
        if len(phase_history) < 2:
            return 0.5
        
        # Подсчитываем последовательные фазы одного типа
        consistent_sequences = 0
        total_sequences = 0
        
        prev_phase = None
        current_sequence_length = 0
        
        for phase_data in phase_history:
            phase = phase_data["phase"]
            
            # Группируем execution_up с accumulation, execution_down с distribution
            normalized_phase = "accumulation" if phase in ("accumulation", "execution_up") else \
                              "distribution" if phase in ("distribution", "execution_down") else "neutral"
            
            if normalized_phase == prev_phase:
                current_sequence_length += 1
            else:
                if prev_phase and current_sequence_length > 0:
                    total_sequences += 1
                    if current_sequence_length >= 2:  # Последовательность из 2+ фаз
                        consistent_sequences += 1
                
                prev_phase = normalized_phase
                current_sequence_length = 1
        
        # Последняя последовательность
        if prev_phase and current_sequence_length >= 2:
            consistent_sequences += 1
        if prev_phase:
            total_sequences += 1
        
        if total_sequences == 0:
            return 0.5
        
        consistency = consistent_sequences / total_sequences
        return consistency

