# 🗂 Проект: SmartMoneyAI v3 (новое ядро)

## 📁 1. Корневая структура

```
smartmoneyai/
│
├── main.py                     # Главная точка входа
├── config.py                   # Настройки проекта
├── requirements.txt            # Зависимости
├── README.md                   # Документация
│
├── data/                       # Исторические и временные данные
│   ├── cache/                  # Кэш ответов биржи / индикаторов
│   └── samples/                # Примеры данных для локального теста
│
├── logs/
│   └── smartmoney.log          # Логи работы
│
├── modules/                    # Основная логика — все алгоритмы
│   ├── liquidity/              # НОВЫЙ Liquidity Engine
│   ├── svd/                    # Smart Volume Dynamics Engine
│   ├── market_structure/       # Определение структуры, swing, BOS/CHoCH
│   ├── ta_engine/              # TA Engine v3 (минималистичная версия)
│   ├── decision/               # Decision Engine v3 (фильтрация)
│   ├── ai_explanations/        # AI генерация объяснений на русском
│   └── utils/                  # Разные утилиты: математика, фильтры, анализ
│
├── api/                        # Связь с биржами
│   ├── bingx_client.py         # BingX REST + WebSocket
│   ├── data_feed.py            # Унифицированный загрузчик данных
│   └── websocket_manager.py    # Обработка WebSocket каналов
│
├── bot/                        # Telegram-бот
│   ├── handlers.py             # Обработка команд
│   ├── notifications.py        # Отправка сигналов и ИИ-оповещений
│   └── formatting/             # Форматирование сообщений
│
└── tests/                      # Локальные тесты
```

## 🧩 2. Детализированная структура модулей

### 📁 modules/liquidity/

Тут живёт наш новый Liquidity Engine v1.0–3.0

```
liquidity/
│
├── engine.py               # Основной алгоритм Liquidity Engine
├── detector_stops.py       # Поиск стопов и ликвидаций
├── detector_heatmap.py     # Детекция кластеров лимиток
├── imbalance.py            # Подсчёт дисбаланса вверх/вниз
└── scoring.py              # Система весов и Confidence Score
```

### 📁 modules/svd/

Smart Volume Dynamics — выявление поглощений, дельты, агрессии.

```
svd/
│
├── svd_engine.py
├── delta.py
├── absorption.py
├── aggression.py
├── velocity.py
└── svd_score.py
```

### 📁 modules/market_structure/

```
market_structure/
│
├── market_structure_engine.py
├── swings.py               # Swing high/low
├── trend.py                # TF bias, тренд
├── range.py                # Боковой диапазон
├── fvg.py                  # Fair Value Gaps
└── orderblocks.py          # Order Blocks
```

### 📁 modules/ta_engine/

Новый облегчённый TA Engine:

```
ta_engine/
│
├── ta_engine.py
├── ema.py
├── rsi.py
└── patterns.py
```

### 📁 modules/decision/

Новый Decision Engine v3.0 (очень чистая логика):

```
decision/
│
├── decision_engine.py
└── risk_filters.py
```

### 📁 modules/ai_explanations/

Генерация текстов на русском:

```
ai_explanations/
│
├── ai_explainer.py
└── text_templates.py
```

### 📁 modules/utils/

Вспомогательные инструменты:

```
utils/
│
├── math_tools.py
├── smoothing.py
├── time_tools.py
├── merge_data.py
└── validators.py
```

## 🛰 3. API / Интерфейс с биржами

### 📁 api/

```
api/
│
├── bingx_client.py        # REST
├── websocket_manager.py   # WebSocket подписки
└── data_feed.py           # Универсальный загрузчик для модулей
```

## 🤖 4. Telegram бот

### 📁 bot/

```
bot/
│
├── handlers.py
├── notifications.py
├── formatting/
│   ├── signal_formatter.py
│   ├── ai_formatter.py
│   └── chart_previews.py   # опционально
```

## 🔧 5. Тесты

```
tests/
│
├── test_liquidity.py
├── test_svd.py
├── test_structure.py
└── test_decision.py
```

## 🏗️ 6. Главная точка входа

### main.py

- запускает WebSocket подписки
- вызывает Liquidity → SVD → Structure → TA → Decision
- отправляет итог в Telegram

